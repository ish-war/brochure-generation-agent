# embd_agent.py
import json
import os
from pathlib import Path
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv
load_dotenv()


def run_embedding(job_dir: str):
    job_dir = Path(job_dir)
    chunks_path = job_dir / "chunks.jsonl"
    chroma_dir = job_dir / "chroma_db"

    if not chunks_path.exists():
        print(f"❌ chunks.jsonl not found in {job_dir}")
        return

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment. Please set it.")
        return

    # Load chunks
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]

    docs = [Document(page_content=c["text"], metadata=c["metadata"]) for c in chunks]

    print(f"🔄 Creating embeddings for {len(docs)} chunks...")
    embeddings = OpenAIEmbeddings(api_key=api_key)
    vectordb = Chroma.from_documents(docs, embedding=embeddings, persist_directory=str(chroma_dir))
    vectordb.persist()
    print(f"✅ Embeddings created and saved to {chroma_dir}")


def get_latest_job_dir(base_dir="jobss"):
    base = Path(base_dir)
    if not base.exists():
        return None
    jobss = sorted(base.glob("*"), key=os.path.getmtime, reverse=True)
    return jobss[0] if jobss else None


if __name__ == "__main__":
    latest_job = get_latest_job_dir()
    if latest_job:
        print(f"🚀 Running embedder on latest job: {latest_job}")
        run_embedding(latest_job)
    else:
        print("❌ No job directory found in jobss/")
