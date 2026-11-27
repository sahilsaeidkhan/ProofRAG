import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.retrieval import search
from src.generation import generate_answer, verify_answer, reformulate, REFUSAL_TEXT, llm, _to_text
from src.config import THRESHOLD


class RagState(TypedDict):
    question: str
    work_question: str
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
    history: Annotated[list, operator.add]


def rewrite_node(state):
    q = state["question"]
    if not state["history"]:
        return {"work_question": q}
    past = "\n".join(f"User: {h['question']}\nAssistant: {h['answer']}" for h in state["history"][-3:])
    prompt = (f"Chat history:\n{past}\n\nFollow-up question: {q}\n\n"
              "Rewrite the follow-up question as a complete standalone question that keeps all "
              "needed context from the history. Reply with only the rewritten question.")
    standalone = _to_text(llm.invoke(prompt)).strip()
    return {"work_question": standalone}


def search_node(state):
    results = search(state["work_question"])
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
    fixed = reformulate(state["work_question"], style=0)
    return {"work_question": fixed, "corrected_question": fixed, "correction_tried": True}


def generate_node(state):
    answer = generate_answer(state["work_question"], state["docs"], strict=state["strict"])
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


def record_node(state):
    return {"history": [{"question": state["question"], "answer": state["answer"]}]}


def route_after_search(state):
    if state["best_score"] >= THRESHOLD:
        return "generate"
    if not state["correction_tried"]:
        return "correct"
    return "escalate"


def route_after_verify(state):
    if state["status"] in ("refused_by_model", "answered", "escalated_failed_verification"):
        return "record"
    return "generate"


builder = StateGraph(RagState)
builder.add_node("rewrite", rewrite_node)
builder.add_node("search", search_node)
builder.add_node("correct", correct_node)
builder.add_node("generate", generate_node)
builder.add_node("verify", verify_node)
builder.add_node("escalate", escalate_node)
builder.add_node("record", record_node)
builder.add_edge(START, "rewrite")
builder.add_edge("rewrite", "search")
builder.add_conditional_edges("search", route_after_search,
                              {"generate": "generate", "correct": "correct", "escalate": "escalate"})
builder.add_edge("correct", "search")
builder.add_edge("generate", "verify")
builder.add_conditional_edges("verify", route_after_verify,
                              {"generate": "generate", "record": "record"})
builder.add_edge("escalate", "record")
builder.add_edge("record", END)
graph = builder.compile(checkpointer=MemorySaver())


def ask_graph(question, thread_id="default"):
    start = {"question": question, "work_question": "", "corrected_question": None, "docs": [],
             "sources": [], "best_score": 0.0, "answer": "", "status": "",
             "correction_tried": False, "strict": False, "attempts": 0, "verified": False}
    config = {"configurable": {"thread_id": thread_id}}
    final = graph.invoke(start, config)
    return {"answer": final["answer"], "sources": final["sources"], "status": final["status"],
            "best_score": final["best_score"], "corrected_question": final["corrected_question"],
            "question_used": final["work_question"]}