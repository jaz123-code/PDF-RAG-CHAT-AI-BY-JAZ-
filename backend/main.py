import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import Query
import ollama 
import chromadb

# ------------------------
# ENV SETUP
# ------------------------

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable not set")

# ------------------------
# FASTAPI APP
# ------------------------

app = FastAPI()
class QueryModel(BaseModel):
    query: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
try :
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


# ------------------------
# CHROMA DB (PERSISTENT)
# ------------------------

chroma_client = chromadb.PersistentClient(path="vectorstore")

collection = chroma_client.get_or_create_collection(
    name="rag_multi_pdf",
    metadata={"hnsw:space": "cosine"}
)

# ------------------------
# UTILS
# ------------------------

def get_embedding(text: str):
    try:
        response = ollama.embeddings(
            model="nomic-embed-text",
            prompt=text
        )
        return response["embedding"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------
# PDF UPLOAD (MULTI-PDF)
# ------------------------

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    os.makedirs("data", exist_ok=True)
    file_path = f"data/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    reader = PdfReader(file_path)
    full_text = ""

    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_text(full_text)

    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)

        collection.add(
            ids=[f"{file.filename}_{i}"],   # UNIQUE ID
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[{"source": file.filename}]
        )

    return {
        "status": "success",
        "file": file.filename,
        "chunks_added": len(chunks)
    }

# ------------------------
# NORMAL ASK ENDPOINT
# ------------------------

@app.post("/ask")
async def ask_question(query: QueryModel):
    query_embedding = get_embedding(query.query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    top_chunks = results["documents"][0]
    context = "\n\n".join(top_chunks)

    prompt = f"""
Answer ONLY using the context below.

CONTEXT:
{context}

QUESTION:
{query}

If the answer is not found, say: "Not found in uploaded PDFs."
"""

    response = ollama.chat(
        model="llama2",
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "answer": response["message"]["content"],
        "sources": results["metadatas"][0]
    }

# ------------------------
# STREAMING ENDPOINT
# ------------------------

from fastapi import Query

@app.post("/stream")
async def stream_answer(query: str = Query(...)):
    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    context = "\n\n".join(results["documents"][0])

    prompt = f"""
Answer ONLY using the context below.

CONTEXT:
{context}

QUESTION:
{query}

If the answer is not found, say:
"Not found in uploaded PDFs."
"""

    async def event_generator():
        for chunk in ollama.chat(
            model="llama2",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        ):
            yield chunk["message"]["content"]

    return StreamingResponse(event_generator(), media_type="text/plain")
