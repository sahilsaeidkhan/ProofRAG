from langchain_core.documents import Document
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
    raw = _store.similarity_search_with_relevance_scores(question, k=k * 2)
    results = []
    seen = set()
    for doc, score in raw:
        if doc.metadata.get("kind") == "faq":
            doc = Document(
                page_content=doc.metadata["chunk_text"],
                metadata={"title": doc.metadata.get("title", ""),
                          "source": doc.metadata.get("source", ""),
                          "file": doc.metadata.get("file", "")},
            )
        key = doc.page_content[:100]
        if key in seen:
            continue
        seen.add(key)
        results.append((doc, score))
        if len(results) == k:
            break
    return results