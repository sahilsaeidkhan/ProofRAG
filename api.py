from fastapi import FastAPI
from pydantic import BaseModel

from src.graph import ask_graph

app = FastAPI(title="ProofRAG API")


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(req: AskRequest):
    return ask_graph(req.question)