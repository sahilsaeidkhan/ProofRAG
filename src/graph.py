from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from src.retrieval import search
from src.generation import generate_answer, verify_answer, reformulate, REFUSAL_TEXT
from src.config import THRESHOLD


class RagState(TypedDict):
    question: str
    corrected_question: str
    docs: list
    sources: list
    best_score: float
    answer: str
    status: str
    correction_tried: bool
    strict: bool
    attempts: int
    verified: bool


def search_node(state):
    results = search(state["question"])
    docs = [d for d, s in results]
    best = float(results[0][1]) if results else 0.0
    sources = []
    seen = set()
    for d in docs:
        key = (d.metadata.get("title", ""), d.metadata.get("file", ""))
        if key not in seen:
            seen.add(key)
            sources.append({"title": d.metadata.get("title", ""),
                            "source": d.metadata.get("source", ""),
                            "file": d.metadata.get("file", "")})
    return {"docs": docs, "best_score": best, "sources": sources}


def correct_node(state):
    fixed = reformulate(state["question"], style=0)
    return {"question": fixed, "corrected_question": fixed, "correction_tried": True}


def generate_node(state):
    answer = generate_answer(state["question"], state["docs"], strict=state["strict"])
    return {"answer": answer}


def verify_node(state):
    if state["answer"].strip() == REFUSAL_TEXT:
        return {"status": "refused_by_model", "verified": False}
    if verify_answer(state["docs"], state["answer"]):
        return {"status": "answered", "verified": True}
    if state["attempts"] < 1:
        return {"verified": False, "attempts": state["attempts"] + 1, "strict": True}
    return {"status": "escalated_failed_verification", "verified": False}


def escalate_node(state):
    return {"answer": REFUSAL_TEXT, "status": "escalated_low_confidence"}


def route_after_search(state):
    if state["best_score"] >= THRESHOLD:
        return "generate"
    if not state["correction_tried"]:
        return "correct"
    return "escalate"


def route_after_verify(state):
    if state["status"] in ("refused_by_model", "answered", "escalated_failed_verification"):
        return END
    return "generate"


builder = StateGraph(RagState)
builder.add_node("search", search_node)
builder.add_node("correct", correct_node)
builder.add_node("generate", generate_node)
builder.add_node("verify", verify_node)
builder.add_node("escalate", escalate_node)
builder.add_edge(START, "search")
builder.add_conditional_edges("search", route_after_search,
                              {"generate": "generate", "correct": "correct", "escalate": "escalate"})
builder.add_edge("correct", "search")
builder.add_edge("generate", "verify")
builder.add_conditional_edges("verify", route_after_verify,
                              {"generate": "generate", END: END})
builder.add_edge("escalate", END)
graph = builder.compile()


def ask_graph(question):
    start = {"question": question, "corrected_question": None, "docs": [], "sources": [],
             "best_score": 0.0, "answer": "", "status": "", "correction_tried": False,
             "strict": False, "attempts": 0, "verified": False}
    final = graph.invoke(start)
    return {"answer": final["answer"], "sources": final["sources"], "status": final["status"],
            "best_score": final["best_score"], "corrected_question": final["corrected_question"]}