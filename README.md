# ProofRAG




Support teams answer the same questions again and again. The answers are already written down somewhere, in a help doc, a policy PDF, an FAQ page. Finding the right one takes time, and a normal chatbot is worse, because when it does not know the answer it just makes one up.

ProofRAG is my attempt at fixing that. You give it company documents. It answers questions only from those documents, and it shows the source with every answer. If the answer is not in the documents, it says so, or passes the question to a human. It does not guess.

## Status: work in progress. I am learning RAG from scratch while building this, so I am building it in phases and writing down what works and what does not.

## The problem in numbers
Knowledge workers spend about 1.8 hours a day just looking for information inside their own company (McKinsey). Support teams feel the same problem from the other side, the same basic questions arriving every day. A system that answers from verified documents, with sources, attacks both sides of it.

## How it will work
Documents come in as PDFs and help pages. They get split into small chunks, turned into embeddings, and stored in a vector database. When someone asks a question, the system finds the most relevant chunks first, then asks the language model to answer using only those chunks. After the answer is generated, a second check makes sure the answer is actually supported by the chunks. Low confidence questions get flagged for a human instead of being sent out as they are.

## Build phases
Phase 1. Basic pipeline. Load documents, chunk them, store embeddings, retrieve, answer. Phase 2. Better retrieval. Hybrid search, reranking, conversation memory, self verification, one advanced trick (HyDE or multi query) with measurements. Phase 3. Evaluation. A fixed set of 50 to 100 questions, checked for correct answers and correct sources. Latency and cost recorded. Phase 4. Production layer. FastAPI backend, Docker, AWS deployment (S3 for documents, EC2 for the API), guardrails, audit logs, tests, CI. Phase 5. Finish. Architecture diagram, live demo, demo video.

## Tech I plan to use
Python, LangChain, Chroma first and Pinecone or pgvector later, FastAPI, Docker, AWS. I will change this list if something does not earn its place.

# Data Source 
- Notion Help Center

## Honest notes
The numbers section will stay empty until the evaluation phase is actually done. I would rather show real measured results late than invent good looking ones early.

Built by Sahil Saeid, learning in public.