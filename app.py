from flask import Flask, render_template, request, jsonify
import requests
import os
import chromadb

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

app = Flask(__name__)
chat_history = []

# Upload folder
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ChromaDB
chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection(name="pdf_docs")

# Embedding model
embedding_model = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- PDF Upload ----------------
@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():

    if "pdf" not in request.files:
        return jsonify({"message": "No PDF uploaded"})

    pdf = request.files["pdf"]

    if pdf.filename == "":
        return jsonify({"message": "No file selected"})

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], pdf.filename)
    pdf.save(filepath)

    # Load PDF
    loader = PyPDFLoader(filepath)
    documents = loader.load()

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    pdf_chunks = text_splitter.split_documents(documents)

    # Clear previous vectors
    if collection.count() > 0:
        ids = collection.get()["ids"]
        if ids:
            collection.delete(ids=ids)

    # Store chunks
    for i, chunk in enumerate(pdf_chunks):

        embedding = embedding_model.embed_query(chunk.page_content)

        collection.add(
    ids=[str(i)],
    documents=[chunk.page_content],
    embeddings=[embedding],
    metadatas=[{
        "page": chunk.metadata.get("page", 0) + 1
    }]
)

    print(f"Total Chunks: {len(pdf_chunks)}")

    return jsonify({
        "message": f"PDF uploaded successfully! {len(pdf_chunks)} chunks stored."
    })


# ---------------- Chat ----------------
@app.route("/chat", methods=["POST"])
def chat():

    global chat_history

    user_message = request.json["message"]
    mode = request.json.get("mode", "friendly")

    # Search in ChromaDB
    query_embedding = embedding_model.embed_query(user_message)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    page_number = "Unknown"
    context = ""

    if results["metadatas"] and len(results["metadatas"][0]) > 0:
        page_number = results["metadatas"][0][0]["page"]

    if results["documents"] and len(results["documents"][0]) > 0:
        context = "\n\n".join(results["documents"][0])
    else:
        context = "No relevant information found."

    prompt = f"""
You are a PDF Question Answering Assistant.

Use ONLY the information provided in the PDF Context.

Rules:
1. Answer ONLY from the PDF Context.
2. Do NOT use your own knowledge.
3. If the answer is not found in the PDF Context, reply exactly:
"I couldn't find this information in the uploaded PDF."

PDF Context:
{context}

User Question:
{user_message}

Answer:
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:1b",
                "prompt": prompt,
                "stream": False
            }
        )

        bot_reply = response.json()["response"]

    except Exception as e:
        print(e)
        bot_reply = "Something went wrong while generating the response."

    chat_history.append({
        "role": "user",
        "message": user_message
    })

    chat_history.append({
        "role": "assistant",
        "message": bot_reply
    })

    return jsonify({
        "reply": bot_reply,
        "source": "Uploaded PDF",
        "page": page_number,
        "chat_history": chat_history
    })
if __name__ == "__main__":
    app.run(debug=True)

       