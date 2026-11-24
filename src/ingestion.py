import json

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from src.config import RAW_DIR, INDEX_DIR, DATA_DIR, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP


def load_documents():
    docs = []
    for path in sorted(RAW_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        title = lines[0].replace("#", "").strip()
        source = ""
        for line in lines[1:4]:
            if line.startswith("Source:"):
                source = line.replace("Source:", "").strip()
                break
        docs.append(Document(
            page_content=text,
            metadata={"title": title, "source": source, "file": path.name},
        ))
    return docs


def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(docs)


def add_faq_entries(chunks):
    faq_file = DATA_DIR / "faq_questions.json"
    if not faq_file.exists():
        return []
    all_questions = json.loads(faq_file.read_text(encoding="utf-8"))
    entries = []
    for i, questions in enumerate(all_questions):
        if i >= len(chunks):
            break
        chunk = chunks[i]
        for q in questions:
            entries.append(Document(
                page_content=q,
                metadata={**chunk.metadata, "kind": "faq", "chunk_text": chunk.page_content},
            ))
    return entries


def build_index(chunks):
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    store = FAISS.from_documents(chunks, embeddings)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    store.save_local(str(INDEX_DIR))
    return store


if __name__ == "__main__":
    docs = load_documents()
    print("Loaded documents:", len(docs))
    chunks = split_documents(docs)
    print("Chunks:", len(chunks))
    extras = add_faq_entries(chunks)
    print("FAQ entries:", len(extras))
    build_index(chunks + extras)
    print("Index saved to", INDEX_DIR)