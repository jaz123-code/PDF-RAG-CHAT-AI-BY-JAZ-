import os
from collections import defaultdict
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
import ollama

# -----------------------------
# APP SETUP
# -----------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# VECTOR DATABASE (CHROMADB)
# -----------------------------

chroma_client = chromadb.PersistentClient(path="vectorstore")

collection = chroma_client.get_or_create_collection(
    name="rag_multi_pdf",
    metadata={"hnsw:space": "cosine"}
)

# -----------------------------
# CHAT MEMORY (SESSION BASED)
# -----------------------------

chat_sessions = defaultdict(list)
MAX_HISTORY = 6  # last 3 user + 3 assistant messages

# -----------------------------
# EMBEDDINGS (OLLAMA)
# -----------------------------

def get_embedding(text: str):
    try:
        response = ollama.embeddings(
            model="nomic-embed-text",
            prompt=text
        )
        return response["embedding"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# PDF UPLOAD (MULTI PDF)
# -----------------------------

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

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
            ids=[f"{file.filename}_{i}"],
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[{"source": file.filename}]
        )

    return {
        "status": "success",
        "file": file.filename,
        "chunks_added": len(chunks)
    }

# -----------------------------
# STREAMING CHAT WITH:
# - RAG
# - PDF FILTERING
# - CHAT MEMORY
# -----------------------------

@app.post("/stream")
async def stream_answer(
    query: str = Query(...),
    session_id: str = Query(...),
    source: str | None = Query(None),
):
    # 1️⃣ Embed query
    query_embedding = get_embedding(query)

    # 2️⃣ Retrieve documents (with optional PDF filter)
    if source:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            where={"source": source}
        )
    else:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

    if not results["documents"][0]:
        return StreamingResponse(
            iter(["Not found in uploaded PDFs."]),
            media_type="text/plain"
        )

    context = "\n\n".join(results["documents"][0])

    # 3️⃣ Load recent chat history
    history = chat_sessions[session_id][-MAX_HISTORY:]

    # 4️⃣ Build messages
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant. Answer strictly using the provided document context."
        },
        {
            "role": "system",
            "content": f"DOCUMENT CONTEXT:\n{context}"
        },
    ]

    messages.extend(history)
    messages.append({"role": "user", "content": query})

    assistant_reply = ""

    # 5️⃣ Stream response + save memory
    async def event_generator():
        nonlocal assistant_reply
        for chunk in ollama.chat(
            model="llama3",
            messages=messages,
            stream=True
        ):
            delta = chunk["message"]["content"]
            assistant_reply += delta
            yield delta

        # Save conversation turn
        chat_sessions[session_id].append(
            {"role": "user", "content": query}
        )
        chat_sessions[session_id].append(
            {"role": "assistant", "content": assistant_reply}
        )

    return StreamingResponse(event_generator(), media_type="text/plain")

