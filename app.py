import streamlit as st
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq

load_dotenv()

st.title("ProofRAG")
st.write("Ask question from Notion help documents — answers only from documents with sources.")

@st.cache_resource
def load_system():
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vector_store = FAISS.load_local(
        "data/faiss_index", embedding_model,
        allow_dangerous_deserialization=True
    )
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    return vector_store, llm

vector_store, llm = load_system()

question = st.text_input("Your question")

if question:
    docs = vector_store.similarity_search(question, k=3)
    context = "\n\n".join(d.page_content for d in docs)

    prompt = f"""Answer the question using ONLY the context below.
If the answer is not in the context, say exactly: I don't have this information in the documents.

Context:
{context}

Question: {question}

Answer:"""

    response = llm.invoke(prompt)
    st.write(response.content)

    st.write("### Sources")
    seen = set()
    for d in docs:
        src = d.metadata["source"]
        if src not in seen:
            seen.add(src)
            st.write("-", d.metadata["title"], "|", src)
