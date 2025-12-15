# 📄 AI Multi-PDF RAG Chatbot (Local LLM)

A full-stack AI application that allows users to upload multiple PDFs and ask
natural-language questions over them using Retrieval-Augmented Generation (RAG).
The system runs **entirely locally** using a local LLM (Ollama), with streaming
responses and a modern chat UI.

---

## 🚀 Features

- 📂 Upload and index **multiple PDFs**
- 🔎 Semantic search using **vector embeddings**
- 🧠 Retrieval-Augmented Generation (RAG)
- 💬 **Streaming chat responses** (real-time)
- 📝 **Markdown & code-block rendering**
- ⚡ Local LLM inference using **Ollama** (no API cost)
- 💾 Persistent vector storage with **ChromaDB**
- 🌙 Modern full-screen React UI

---

## 🧠 Tech Stack

**Frontend**
- React (Vite)
- Streaming Fetch API
- react-markdown + remark-gfm

**Backend**
- FastAPI
- ChromaDB (persistent vector store)
- PyPDF (PDF parsing)
- Ollama (local LLM + embeddings)

**Models**
- LLM: `llama2`
- Embeddings: `nomic-embed-text`

---

## 🏗 Architecture
React (Chat UI)
↓
FastAPI (API + Streaming)
↓
ChromaDB (Vector Store)
↓
Ollama (Local LLM & Embeddings)


---

## ⚙️ How It Works

1. User uploads one or more PDFs
2. PDFs are chunked and embedded
3. Embeddings are stored in ChromaDB
4. User asks a question
5. Relevant chunks are retrieved via cosine similarity
6. Context is injected into the prompt
7. Local LLM generates a **streamed response**

---

## 🧪 Example Questions

- “Summarize this document”
- “What is this PDF mainly about?”
- “Explain this concept with a code example”
- “Compare topics across multiple PDFs”

---

## 📌 Why This Project Matters

This project demonstrates:
- Real-world RAG system design
- Streaming AI UX
- LLM provider abstraction (cloud → local)
- Cost-efficient AI engineering
- End-to-end system thinking

---

## 📸 Screenshots

> See screenshots folder for UI and architecture visuals.

---

## 🧩 Future Improvements

- Document-level filtering
- Chat history & memory
- Authentication
- Deployment (Vercel + Render)

---
## 🌐 Live Demo

Frontend is deployed on Vercel.

> ⚠️ Note: Backend runs locally using a local LLM (Ollama) and is not publicly hosted.

Live URL: pdf-rag-chat-ai-by-jaz.vercel.app


## 👨‍💻 Author

Built by **[Muhammed jazim T]**  
AI / ML Engineering Enthusiast# PDF-RAG-CHAT-AI-BY-JAZ-
