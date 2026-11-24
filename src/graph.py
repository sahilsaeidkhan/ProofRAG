from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from src.retrieval import search
from src.generation import generate_answer, verify_answer, REFUSAL_TEXT


class RagState(TypedDict):
    question: str
    docs: list
    best_score: float
    answer: str
    status: str


def search_node(state):
    results = search(state["question"])
    docs = [d for d, s in results]
    best = results[0][1] if results else 0.0
    return {"docs": docs, "best_score": best}


def generate_node(state):
    answer = generate_answer(state["question"], state["docs"])
    return {"answer": answer}


def verify_node(state):
    if state["answer"].strip() == REFUSAL_TEXT:
        return {"status": "refused_by_model"}
    if verify_answer(state["docs"], state["answer"]):
        return {"status": "answered"}
    return {"status": "escalated_failed_verification"}


builder = StateGraph(RagState)
builder.add_node("search", search_node)
builder.add_node("generate", generate_node)
builder.add_node("verify", verify_node)
builder.add_edge(START, "search")
builder.add_edge("search", "generate")
builder.add_edge("generate", "verify")
builder.add_edge("verify", END)
graph = builder.compile()


def ask_graph(question):
    final = graph.invoke({"question": question})
    return {"answer": final["answer"], "status": final["status"], "best_score": final["best_score"]}