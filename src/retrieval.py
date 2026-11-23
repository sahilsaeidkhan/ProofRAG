from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from src.config import INDEX_DIR, EMBEDDING_MODEL, TOP_K

_embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
_store = FAISS.load_local(
    str(INDEX_DIR),
    _embeddings,
    allow_dangerous_deserialization=True,
)


def search(question, k=TOP_K):
    return _store.similarity_search_with_relevance_scores(question, k=k)
