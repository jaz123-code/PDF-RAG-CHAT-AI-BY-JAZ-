import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";


function App() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [pdfFile, setPdfFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");

  const chatEndRef = useRef(null);

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Upload PDF
  const handlePdfUpload = async () => {
    if (!pdfFile) {
      alert("Please select a PDF first");
      return;
    }

    const formData = new FormData();
    formData.append("file", pdfFile);

    try {
      const res = await fetch("http://127.0.0.1:8000/upload_pdf", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setUploadStatus(
        `✅ ${data.file} uploaded (${data.chunks_added} chunks)`
      );
    } catch {
      setUploadStatus("❌ Upload failed");
    }
  };

  // Ask question (streaming)
  const handleAsk = async () => {
    if (!question.trim()) return;

    const userMessage = { role: "user", content: question };
    const aiMessage = { role: "ai", content: "" };

    setMessages((prev) => [...prev, userMessage, aiMessage]);
    setQuestion("");
    setLoading(true);

    const response = await fetch(
      "http://127.0.0.1:8000/stream?query=" +
        encodeURIComponent(userMessage.content),
      { method: "POST" }
    );

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].content += chunk;
        return updated;
      });
    }

    setLoading(false);
  };

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <h2 style={styles.header}>📄 AI Multi-PDF Chatbot</h2>

        {/* Upload */}
        <div style={styles.uploadBox}>
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setPdfFile(e.target.files[0])}
          />
          <button style={styles.uploadButton} onClick={handlePdfUpload}>
            Upload PDF
          </button>
        </div>

        {uploadStatus && (
          <div style={styles.uploadStatus}>{uploadStatus}</div>
        )}

        {/* Chat */}
        <div style={styles.chatBox}>
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                ...styles.bubble,
                alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                backgroundColor:
                  msg.role === "user" ? "#2563eb" : "#1f2937",
                color: msg.role === "user" ? "#fff" : "#e5e7eb",
              }}
            >
              {msg.role === "ai" ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ inline, children }) {
                      return inline ? (
                        <code style={styles.inlineCode}>{children}</code>
                      ) : (
                        <pre style={styles.codeBlock}>
                          <code>{children}</code>
                        </pre>
                      );
                    },
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              ):(
                msg.content
              )}
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div style={styles.inputArea}>
          <input
            value={question}
            placeholder="Ask something from uploaded PDFs…"
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            style={styles.input}
          />
          <button onClick={handleAsk} style={styles.sendButton}>
            Send
          </button>
        </div>

        {loading && (
          <p style={styles.thinking}>💬 Generating response…</p>
        )}
      </div>
    </div>
  );
}

export default App;

/* ---------------- STYLES ---------------- */

const styles = {
  page: {
    minHeight: "100vh",
    width: "100vw",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#0f0f10",
  },

  container: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    padding: "24px",
    fontFamily:
      "Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
    backgroundColor: "#111827",
  },


  header: {
    textAlign: "center",
    marginBottom: "20px",
    fontSize: "26px",
    fontWeight: "600",
    color: "#f9fafb",
  },

  uploadBox: {
    display: "flex",
    justifyContent: "center",
    gap: "12px",
    marginBottom: "12px",
  },

  uploadButton: {
    padding: "8px 14px",
    borderRadius: "8px",
    border: "none",
    backgroundColor: "#374151",
    color: "#f9fafb",
    cursor: "pointer",
  },

  uploadStatus: {
    textAlign: "center",
    fontSize: "13px",
    color: "#9ca3af",
    marginBottom: "12px",
  },

  chatBox: {
    flex: 1,
    backgroundColor: "#020617",
    borderRadius: "12px",
    padding: "16px",
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },


  bubble: {
    maxWidth: "70%",
    padding: "12px 16px",
    borderRadius: "14px",
    fontSize: "14.5px",
    lineHeight: "1.6",
    whiteSpace: "pre-wrap",
  },

  inputArea: {
    display: "flex",
    gap: "10px",
    marginTop: "16px",
  },


  input: {
    flex: 1,
    padding: "12px",
    borderRadius: "10px",
    border: "1px solid #374151",
    backgroundColor: "#020617",
    color: "#f9fafb",
    outline: "none",
  },

  sendButton: {
    padding: "12px 18px",
    borderRadius: "10px",
    border: "none",
    backgroundColor: "#2563eb",
    color: "#ffffff",
    cursor: "pointer",
    fontWeight: "500",
  },

  thinking: {
    textAlign: "center",
    marginTop: "10px",
    fontSize: "13px",
    color: "#9ca3af",
  },
  codeBlock: {
  backgroundColor: "#020617",
  color: "#e5e7eb",
  padding: "14px",
  borderRadius: "10px",
  fontSize: "13px",
  overflowX: "auto",
  marginTop: "8px",
},

inlineCode: {
  backgroundColor: "#1f2937",
  padding: "2px 6px",
  borderRadius: "6px",
  fontSize: "13px",
},

};
