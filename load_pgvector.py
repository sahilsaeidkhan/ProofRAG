import json

from langchain_huggingface import HuggingFaceEmbeddings

from src.config import DATA_DIR, EMBEDDING_MODEL
from src.db import get_connection
from src.ingestion import load_documents, split_documents


def main():
    docs = load_documents()
    print("Loaded documents:", len(docs))
    chunks = split_documents(docs)
    print("Chunks:", len(chunks))

    faq_file = DATA_DIR / "faq_questions.json"
    all_questions = json.loads(faq_file.read_text(encoding="utf-8"))

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    chunk_vectors = embeddings.embed_documents([c.page_content for c in chunks])
    print("Chunk embeddings ready:", len(chunk_vectors))

    flat_questions = []
    flat_chunk_ids = []
    for i, questions in enumerate(all_questions):
        if i >= len(chunks):
            break
        for q in questions:
            flat_questions.append(q)
            flat_chunk_ids.append(i)
    faq_vectors = embeddings.embed_documents(flat_questions)
    print("FAQ embeddings ready:", len(faq_vectors))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute("DROP TABLE IF EXISTS faq_questions")
    cur.execute("DROP TABLE IF EXISTS chunks")
    cur.execute("""
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY,
            title TEXT,
            source TEXT,
            file TEXT,
            text TEXT,
            embedding vector(384)
        )
    """)
    cur.execute("""
        CREATE TABLE faq_questions (
            id SERIAL PRIMARY KEY,
            question TEXT,
            chunk_id INTEGER REFERENCES chunks(id),
            embedding vector(384)
        )
    """)

    chunk_rows = []
    for i, (chunk, vector) in enumerate(zip(chunks, chunk_vectors)):
        chunk_rows.append((
            i,
            chunk.metadata.get("title", ""),
            chunk.metadata.get("source", ""),
            chunk.metadata.get("file", ""),
            chunk.page_content,
            str(vector),
        ))
    cur.executemany(
        "INSERT INTO chunks (id, title, source, file, text, embedding) VALUES (%s, %s, %s, %s, %s, %s)",
        chunk_rows,
    )
    print("Chunks inserted:", len(chunk_rows))

    faq_rows = [
        (q, cid, str(v))
        for q, cid, v in zip(flat_questions, flat_chunk_ids, faq_vectors)
    ]
    cur.executemany(
        "INSERT INTO faq_questions (question, chunk_id, embedding) VALUES (%s, %s, %s)",
        faq_rows,
    )
    print("FAQ questions inserted:", len(faq_rows))

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()