from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()

embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
vectordb = Chroma(persist_directory="jobss/20251027_232025_bc7521ff/chroma_db/3e140603-7a3b-4de4-8ccf-0824520c073f", embedding_function=embeddings)

query = "company overview"
results = vectordb.similarity_search(query, k=3)
print(f"Found {len(results)} results")

for i, r in enumerate(results[:2]):
    print(f"\n--- DOC {i+1} ---\n{r.page_content[:500]}")

