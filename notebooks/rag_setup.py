
## Reusable code


import re
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_groq import ChatGroq
from sentence_transformers import CrossEncoder

load_dotenv(BASE_DIR / ".env")

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vector_store = FAISS.load_local(
    str(BASE_DIR / "data" / "faiss_index")
,
    embedding_model,
    allow_dangerous_deserialization=True
)

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

all_docs = list(vector_store.docstore._dict.values())

bm25_retriever = BM25Retriever.from_documents(all_docs)
bm25_retriever.k = 10

print("Setup ready. Chunks:", vector_store.index.ntotal)



import re

def make_queries(question):
    mq_prompt = f"""Write 3 different versions of this question using different words, so a search system can find the answer in help documents.

Question: {question}
Write only the 3 questions , one per line , no numbering"""
    text = llm.invoke(mq_prompt).content
    lines= []

    for l in text.strip().split('\n'):
        l = re.sub(r"^\d+[\.\)]\s*", "", l.strip()).strip("- ").strip()
        if l :
            lines.append(l)
    return [question] + lines[:3]

def pool_for(queries):
    pool, seen = [], set()
    for q in queries:
        docs = vector_store.similarity_search(q, k=5) + bm25_retriever.invoke(q)[:5]
        for d in docs:
            if d.page_content not in seen:
                seen.add(d.page_content)
                pool.append(d)
    return pool
