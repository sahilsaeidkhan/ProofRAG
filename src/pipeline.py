from src.config import THRESHOLD
from src.retrieval import search
from src.generation import generate_answer, verify_answer, reformulate, REFUSAL_TEXT


def ask(question):
    results = search(question)
    if not results:
        return {"answer": REFUSAL_TEXT, "sources": [], "status": "refused_no_results",
                "best_score": 0.0, "corrected_question": None}

    best = float(results[0][1])
    used_question = question
    corrected = None

    if best < THRESHOLD:
        fixed = reformulate(question, 0)
        if fixed != question:
            results2 = search(fixed)
            if results2 and float(results2[0][1]) > best:
                results = results2
                best = float(results2[0][1])
                used_question = fixed
                corrected = fixed

    docs = [d for d, s in results]

    if best < THRESHOLD:
        return {"answer": REFUSAL_TEXT, "sources": [], "status": "escalated_low_confidence",
                "best_score": best, "corrected_question": corrected}

    answer = generate_answer(used_question, docs)

    if answer.strip() == REFUSAL_TEXT:
        return {"answer": answer, "sources": [], "status": "refused_by_model",
                "best_score": best, "corrected_question": corrected}

    if not verify_answer(docs, answer):
        answer = generate_answer(used_question, docs, strict=True)
        if answer.strip() == REFUSAL_TEXT or not verify_answer(docs, answer):
            return {"answer": REFUSAL_TEXT, "sources": [], "status": "escalated_failed_verification",
                    "best_score": best, "corrected_question": corrected}

    sources = []
    for d in docs:
        s = {"title": d.metadata.get("title", ""), "source": d.metadata.get("source", ""), "file": d.metadata.get("file", "")}
        if s not in sources:
            sources.append(s)

    return {"answer": answer, "sources": sources, "status": "answered",
            "best_score": best, "corrected_question": corrected}
