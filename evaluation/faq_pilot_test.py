import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from src.config import EMBEDDING_MODEL

pack = json.load(open("evaluation/faq_pilot_pack.json", encoding="utf-8"))
print(f"Pilot items: {len(pack)}")

docs = []
for item in pack:
    docs.append(Document(page_content=item["passage_text"],
                         metadata={"kind": "chunk", "golden": item["golden_question"]}))
    for fq in item["faq_questions"]:
        docs.append(Document(page_content=fq,
                             metadata={"kind": "faq", "golden": item["golden_question"]}))
print(f"Index entries: {len(docs)}")

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
store = FAISS.from_documents(docs, embeddings)

lines = []
for item in pack:
    q = item["golden_question"]
    results = store.similarity_search_with_relevance_scores(q, k=3)
    top = results[0]
    faq_hit = any(d.metadata["kind"] == "faq" and d.metadata["golden"] == q for d, s in results)
    chunk_hit = any(d.metadata["kind"] == "chunk" and d.metadata["golden"] == q for d, s in results)
    line = (f"old: {item['score_note']} -> top1 {top[0].metadata['kind']} "
            f"{top[1]:.2f} | faq in top3: {faq_hit} | chunk in top3: {chunk_hit} | {q[:60]}")
    print(line)
    lines.append(line)

Path("evaluation/faq_pilot_result.txt").write_text("\n".join(lines), encoding="utf-8")
print("Done - evaluation/faq_pilot_result.txt")