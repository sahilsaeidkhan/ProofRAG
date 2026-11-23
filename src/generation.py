from langchain_groq import ChatGroq

from src.config import GROQ_API_KEY, LLM_MODEL

REFUSAL_TEXT = "I don't have this information in the documents."

llm = ChatGroq(model=LLM_MODEL, api_key=GROQ_API_KEY)


def build_context(docs):
    return "\n\n".join(d.page_content for d in docs)


def generate_answer(question, docs, strict=False):
    context = build_context(docs)
    extra = ""
    if strict:
        extra = "\nBe extra careful: use only facts written in the context. Do not add anything from your own knowledge."
    prompt = f"""Answer the question using ONLY the context below.
If the answer is not in the context, say exactly: {REFUSAL_TEXT}{extra}

Context:
{context}

Question: {question}

Answer:"""
    return llm.invoke(prompt).content


def verify_answer(docs, answer):
    context = build_context(docs)
    prompt = f"""You are a strict checker. Read the context and the answer.
Reply with exactly one word: SUPPORTED if every claim in the answer is supported by the context, or NOT_SUPPORTED if any claim is not supported.

Context:
{context}

Answer: {answer}

Verdict:"""
    text = llm.invoke(prompt).content.strip().upper()
    return "NOT_SUPPORTED" not in text and "SUPPORTED" in text


REFORMULATE_STYLES = {
    0: "Correct only the spelling mistakes in this question. Do not change any other word, do not reword anything.",
    1: "Rewrite this question using formal words that would appear in help documentation.",
    2: "Rewrite this question in the simplest possible words, as a beginner would ask it.",
}


def reformulate(question, style=0):
    prompt = f"""{REFORMULATE_STYLES[style]}
Write only the rewritten question, nothing else.

Question: {question}"""
    return llm.invoke(prompt).content.strip()
