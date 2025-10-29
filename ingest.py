import os
import json
import uuid
from pathlib import Path
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_core.documents import Document

# Optional: Only used if create_embeddings=True
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma


def load_documents(input_dir: str):
    """
    Loads PDF and DOCX files from the given input directory
    and returns a list of LangChain Document objects.
    """
    docs = []
    for file in os.listdir(input_dir):
        file_path = os.path.join(input_dir, file)
        ext = Path(file).suffix.lower()

        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext == ".docx":
            loader = Docx2txtLoader(file_path)
        else:
            print(f"⚠️ Skipping unsupported file type: {file}")
            continue

        loaded_docs = loader.load()
        for d in loaded_docs:
            d.metadata["source_file"] = file
        docs.extend(loaded_docs)

    print(f"✅ Loaded {len(docs)} documents from {input_dir}")
    return docs


def chunk_documents(docs, chunk_size=1000, chunk_overlap=200):
    """
    Splits documents into smaller overlapping chunks.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_docs = splitter.split_documents(docs)
    print(f"🧩 Split into {len(split_docs)} chunks.")
    return split_docs


def save_chunks(split_docs, job_dir: Path):
    """
    Saves chunks as a JSONL file for later embedding generation.
    """
    chunks_path = job_dir / "chunks.jsonl"
    with open(chunks_path, "w", encoding="utf-8") as f:
        for doc in split_docs:
            json.dump({
                "text": doc.page_content,
                "metadata": doc.metadata
            }, f)
            f.write("\n")
    print(f"💾 Saved chunks to {chunks_path}")
    return chunks_path


def run_ingest(
    input_dir: str,
    output_root: str = "./data/jobs",
    create_embeddings: bool = True
):
    """
    Ingests uploaded documents:
      - Loads PDF/DOCX
      - Splits into chunks
      - Saves chunks to disk
      - (Optional) Creates embeddings and stores them in Chroma

    Returns:
        dict: Job metadata including job_dir, chunk file, and DB path
    """
    os.makedirs(output_root, exist_ok=True)

    # Create a unique job folder
    job_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + str(uuid.uuid4())[:8]
    job_dir = Path(output_root) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # 1️⃣ Load documents
    docs = load_documents(input_dir)

    # 2️⃣ Chunk documents
    split_docs = chunk_documents(docs)

    # 3️⃣ Save chunks to JSONL
    chunks_path = save_chunks(split_docs, job_dir)

    # 4️⃣ Optional: Create embeddings immediately
    chroma_dir = job_dir / "chroma_db"
    vectordb = None
    if create_embeddings:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY not found in environment variables.")
        print("🧠 Generating embeddings using OpenAI...")

        embeddings = OpenAIEmbeddings(api_key=api_key)
        vectordb = Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings,
            persist_directory=str(chroma_dir)
        )
        print(f"✅ Embeddings created and stored in {chroma_dir}")
    else:
        print("⏭️ Skipped embedding generation (handled by embedder_agent).")

    # 5️⃣ Return job info
    return {
        "job_id": job_id,
        "job_dir": str(job_dir),
        "chunks_path": str(chunks_path),
        "chroma_dir": str(chroma_dir),
        "embeddings_created": create_embeddings
    }


if __name__ == "__main__":
    # Example test run
    result = run_ingest(
        input_dir="./data/docs",
        output_root="./jobss",
        create_embeddings=False  # set to True to generate embeddings here
    )
    print(json.dumps(result, indent=2))
