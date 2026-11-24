from langchain_groq import ChatGroq

from src.config import (
    GROQ_API_KEY,
    LLM_MODEL,
    LLM_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)

REFUSAL_TEXT = "I don't have this information in the documents."

if LLM_PROVIDER == "gemini":
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY)
else:
    llm = ChatGroq(model=LLM_MODEL, api_key=GROQ_API_KEY)


def _to_text(response):
    content = response.content
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, dict):
            parts.append(block.get("text", ""))
        else:
            parts.append(getattr(block, "text", ""))
    return "".join(parts)


def build_context(docs):
    return "\n\n".join(d.page_content for d in docs)


def generate_answer(question, docs, strict=False):
    context = build_context(docs)
    extra = ""
    if strict:
        extra = "\nBe extra careful: use only facts written in the context. Do not add anything from your own knowledge."
    prompt = f"""Answer the question using ONLY the context below.
The answer may be written in different words than the question, or spread across several parts of the context. Combine the pieces and answer in your own words.
Refuse only if the information needed is not in the context at all. If you must refuse, say exactly: {REFUSAL_TEXT}{extra}

Context:
{context}

Question: {question}

Answer:"""
    return _to_text(llm.invoke(prompt))


def verify_answer(docs, answer):
    context = build_context(docs)
    prompt = f"""You are a strict checker. Read the context and the answer.
Reply with exactly one word: SUPPORTED if every claim in the answer is supported by the context, or NOT_SUPPORTED if any claim is not supported.

Context:
{context}

Answer: {answer}

Verdict:"""
    text = _to_text(llm.invoke(prompt)).strip().upper()
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
    return _to_text(llm.invoke(prompt)).strip()