import re
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_groq import ChatGroq
from sentence_transformers import CrossEncoder

load_dotenv("../.env")

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vector_store = FAISS.load_local(
    "../data/faiss_index",
    embedding_model,
    allow_dangerous_deserialization=True
)

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

all_docs = list(vector_store.docstore._dict.values())

bm25_retriever = BM25Retriever.from_documents(all_docs)
bm25_retriever.k = 10

print("Setup ready. Chunks:", vector_store.index.ntotal)
