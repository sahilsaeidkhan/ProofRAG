# ProofRAG

Support teams answer the same questions again and again. The answers are already written down somewhere, in a help doc, a policy PDF, an FAQ page. Finding the right one takes time, and a normal chatbot is worse, because when it does not know the answer it just makes one up.

ProofRAG is my attempt at fixing that. You give it company documents. It answers questions only from those documents, and it shows the source with every answer. If the answer is not in the documents, it says so, or passes the question to a human. It does not guess.

Status: Phase 1, Phase 2 and Phase 3 are done. Phase 4 is in progress. The pipeline has been moved out of the notebooks into a proper Python package, and I am running improvement experiments on it now, one change at a time, each one measured on the same fixed test set. The production pieces (API, database, deployment) come after the experiments.

## The problem in numbers

Knowledge workers spend about 1.8 hours a day just looking for information inside their own company (McKinsey). Support teams feel the same problem from the other side, the same basic questions arriving every day. A system that answers from verified documents, with sources, attacks both sides of it.

## How it works

Documents come in as help pages in markdown (PDF support comes later). They get split into small chunks, turned into embeddings, and stored in a vector store. When someone asks a question, the system searches the chunks. A score threshold stops weak matches before they reach the model. If the best score is too low, the system first tries correcting the spelling of the question and searches once more, because a single typo can drag a good question's score from 0.59 down to 0.13. The language model then answers using only the picked chunks. After the answer is generated, a second check makes sure the answer is actually supported by the chunks. If the check fails, the model retries once with a stricter instruction. If it still fails, or confidence is low, the question gets flagged for a human instead of being sent out as it is.

The notebooks also had conversation memory, hybrid search (meaning based search plus BM25 keyword search), a cross encoder reranker, and multi query expansion. Phase 3 measured all of it, and on my data the plain semantic search beat every fancier variant, so semantic search is what the packaged system runs. The rest stays in the notebooks as experiments, with their numbers. Conversation memory comes back later in Phase 4, as part of the agent graph.

Right now the corpus is 25 Notion help articles, kept on my machine only, because they are Notion's content and not mine to redistribute. The code is public, the data is not.

## Evaluation results

Phase 3 used a fixed test set of 100 questions: 65 direct questions, 20 reworded the way a normal user would ask, and 15 questions whose answers are not in the documents at all. Every question has a known correct source, so the scoring is not a matter of opinion.

Retrieval, on the full set: the correct source was in the top 3 chunks for 79 of the 85 answerable questions.

Retrieval, comparing designs, on the first 25 questions: plain semantic search scored 19 out of 20. Hybrid search with reranking, multi query, a bigger reranker, and rank fusion all scored 15 out of 20. The reranker was the main problem. In one case the correct chunk was in the candidate pool and the reranker pushed it down to position 7. A technique that sounds advanced is not automatically better, and now I have numbers instead of an opinion.

Answers, on the full set: 54 answers fully correct, 3 partly correct, and 28 questions refused even though the answer existed in the documents. All 15 no-answer questions were refused safely, 10 by the score threshold and the rest by the model itself after reading the chunks. Zero answers were invented. Not one.

The honest summary: this system does not lie, but it refuses too much. Its worst failures are casually worded questions, the way real users actually talk. One scored 0.05 against a 0.45 threshold even though the answer was sitting in the documents. Fixing that is planned for Phase 4, where a refused question gets retried with different wording before it is escalated to a human.

### Testing the packaged system (104 questions)

For Phase 4 the test set grew to 104 questions. I added three questions with spelling mistakes and one clean version of a question the system used to answer badly, because real users make typos, and I would rather meet that failure in the test set than in production.

Retrieval, at 3 chunks per question: the correct source was in the top 3 for 82 of the 89 answerable questions.

Answers: 55 fully correct, 3 partly correct, and 31 refused even though the answer existed in the documents. Of those 31, the threshold stopped 18 and the model itself refused 13, several of them with the right chunks in front of it and high scores. That one surprised me. The model is sometimes too cautious, and the prompt is now one of the things on my fix list. All 15 no-answer questions were handled safely again. Zero answers were invented.

The threshold analysis was the most useful part of this round. The no-answer questions are not all low scoring. The most dangerous ones, like which AI model Notion AI uses (score 0.63) and the exact price of the Plus plan (0.56), score higher than plenty of good questions, and they already pass the threshold today. The prompt and the verification check are what actually catch them. The threshold mostly blocks good questions asked in casual words. From the score data, lowering the threshold from 0.45 to 0.30 would let 14 more answerable questions through, and the no-answer questions it would newly let through are ones the prompt has already shown it can refuse at even higher scores. That change gets its own measured test run next. No threshold fixes the worst cases though. Two good questions score 0.14 and 0.15, below any sensible line. Those need a different fix, indexing the chunks in question form (FAQ style), which is also planned.

I also tested showing the model 5 chunks instead of 3. Retrieval improved by exactly one question, 83 out of 89. The full answer test at 5 chunks is still pending, because the free API tier ran out of its daily token budget in the middle of the test day (see honest notes).

Latency and cost per question are not measured yet. That is still missing and I am not going to pretend otherwise.

## Build phases

Phase 1. Basic pipeline. Load documents, chunk them, store embeddings, retrieve, answer. **Done.**
Phase 2. Better retrieval. Hybrid search, reranking, conversation memory, self verification, one advanced trick (multi query) with measurements. **Done.**
Phase 3. Evaluation. A fixed set of 100 questions, checked for correct answers and correct sources. **Done.**
Phase 4. Production layer. **In progress.** The pipeline is packaged and the improvement experiments are running. After that: FastAPI backend, Docker, AWS deployment (S3 for documents, PostgreSQL with pgvector on RDS for vectors and app data), guardrails, audit logs, tests, CI. The pipeline also gets rebuilt as an agent graph with LangGraph, which can retry a refused question with different wording before escalating it.
Phase 5. Finish. Architecture diagram, live demo, demo video.

## Tech used so far

Python, LangChain, FAISS (local vector store), BM25 for keyword search, MiniLM embeddings, a cross encoder reranker, Groq running openai/gpt-oss-120b as the language model, Streamlit for a small test UI. Phase 4 moves the vectors to PostgreSQL with pgvector on AWS RDS.

## Data source

- Notion Help Center

## Honest notes

This is not finished. What is measured is written above, including the parts that went badly. I would rather show real results late than invent good looking ones early.

One loose end from earlier is now closed: the corpus folder always had 25 clean files. The extra chunks I saw came from an old saved index, and re-running ingestion fixed it.

The known weakness right now is over-refusal, measured at 31 out of 89 answerable questions on the bigger test set. The fix path is clearer than it was in Phase 3: re-tune the threshold, fix the prompt, index in question form, then add the retry loop. Each one gets measured separately, so I know which one actually worked.

Evaluation runs on the free Groq tier, which allows 200,000 tokens a day. On 23 Nov the day's test runs and restarts used up the whole budget, and one test had to stop at its first question and wait for the next day. Free tiers have real limits. Measuring cost properly is still on my list, and this is exactly why it matters.

Built by Sahil Saeid, learning in public.
