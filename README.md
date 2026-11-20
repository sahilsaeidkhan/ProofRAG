# ProofRAG

Support teams answer the same questions again and again. The answers are already written down somewhere, in a help doc, a policy PDF, an FAQ page. Finding the right one takes time, and a normal chatbot is worse, because when it does not know the answer it just makes one up.

ProofRAG is my attempt at fixing that. You give it company documents. It answers questions only from those documents, and it shows the source with every answer. If the answer is not in the documents, it says so, or passes the question to a human. It does not guess.

Status: Phase 1 and Phase 2 are done. Phase 3 (evaluation) is next. I am learning RAG from scratch while building this, so I am building it in phases and writing down what works and what does not.

## The problem in numbers

Knowledge workers spend about 1.8 hours a day just looking for information inside their own company (McKinsey). Support teams feel the same problem from the other side, the same basic questions arriving every day. A system that answers from verified documents, with sources, attacks both sides of it.

## How it works

Documents come in as help pages in markdown (PDF support comes later). They get split into small chunks, turned into embeddings, and stored in a vector store. When someone asks a question, the system first rewrites follow up questions into full questions using the conversation history. Then it searches in two ways at once, by meaning (vector search) and by exact words (BM25), merges the results, and lets a reranker pick the best chunks. A score threshold stops weak matches before they reach the model. The language model answers using only the picked chunks, and after the answer is generated, a second check makes sure the answer is actually supported by the chunks. If the check fails twice, or confidence is low, the question gets flagged for a human instead of being sent out as it is.

Right now the corpus is 25 Notion help articles, kept on my machine only, because they are Notion's content and not mine to redistribute. The code is public, the data is not.

## Build phases

Phase 1. Basic pipeline. Load documents, chunk them, store embeddings, retrieve, answer. **Done.**
Phase 2. Better retrieval. Hybrid search, reranking, conversation memory, self verification, one advanced trick (multi query) with measurements. **Done.**
Phase 3. Evaluation. A fixed set of 50 to 100 questions, checked for correct answers and correct sources. Latency and cost recorded.
Phase 4. Production layer. FastAPI backend, Docker, AWS deployment (S3 for documents, PostgreSQL with pgvector on RDS for vectors and app data), guardrails, audit logs, tests, CI.
Phase 5. Finish. Architecture diagram, live demo, demo video.

## Tech used so far

Python, LangChain, FAISS (local vector store), BM25 for keyword search, MiniLM embeddings, a cross encoder reranker, Groq running openai/gpt-oss-120b as the language model, Streamlit for a small test UI. Phase 4 moves the vectors to PostgreSQL with pgvector on AWS RDS.

## Data source

- Notion Help Center

## Honest notes

This is not finished, and the numbers section will stay empty until the evaluation phase is actually done. I would rather show real measured results late than invent good looking ones early.

One known loose end: the corpus folder currently loads 27 files where 25 were expected, so there are probably two duplicates in there. Cleaning that up is still on my list.

Built by Sahil Saeid, learning in public.
