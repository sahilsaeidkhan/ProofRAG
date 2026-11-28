import math

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from src.config import TOP_K
from src.db import get_connection

_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

SQRT2 = math.sqrt(2)


def search(question, k=TOP_K):
    """Search chunks and FAQ questions in pgvector.

    Returns a list of (Document, score), best first.
    Score uses squared L2 distance on purpose: the old FAISS index
    returned squared distances, and the threshold + evaluation
    numbers were tuned on that scale, so we keep the same scale.
    """
    q_vector = _embeddings.embed_query(question)
    q_str = str(q_vector)

    sql = """
        SELECT content, title, source, file, score
        FROM (
            SELECT c.text AS content, c.title AS title,
                   c.source AS source, c.file AS file,
                   1 - (POWER(c.embedding <-> %s::vector, 2) / %s) AS score
            FROM chunks c
            UNION ALL
            SELECT c.text AS content, c.title AS title,
                   c.source AS source, c.file AS file,
                   1 - (POWER(f.embedding <-> %s::vector, 2) / %s) AS score
            FROM faq_questions f
            JOIN chunks c ON c.id = f.chunk_id
        ) hits
        ORDER BY score DESC
        LIMIT %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (q_str, SQRT2, q_str, SQRT2, k * 2))
            rows = cur.fetchall()

    results = []
    seen = set()
    for content, title, source, file, score in rows:
        key = content[:100]
        if key in seen:
            continue
        seen.add(key)
        doc = Document(
            page_content=content,
            metadata={"title": title, "source": source, "file": file},
        )
        results.append((doc, float(score)))
        if len(results) >= k:
            break
    return results