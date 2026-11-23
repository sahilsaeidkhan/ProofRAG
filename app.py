import streamlit as st

from src.pipeline import ask

st.title("ProofRAG")
st.write("Answers only from the documents. If the answer is not there, it says so.")

question = st.text_input("Ask a question")

if question:
    with st.spinner("Searching the documents..."):
        result = ask(question)
    st.write(result["answer"])
    if result.get("corrected_question"):
      st.caption(f"Interpreted as: {result['corrected_question']}")

    if result["status"] == "answered":
        st.subheader("Sources")
        for s in result["sources"]:
            st.write(f"- {s['title']} ({s['source']})")
    elif result["status"].startswith("escalated"):
        st.warning("This question has been flagged for a human to answer.")
    st.caption(f"Status: {result['status']} | Best score: {result['best_score']:.2f}")
