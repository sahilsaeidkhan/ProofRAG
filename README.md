# ProofRAG

Support teams answer the same questions again and again. The answers are already written down somewhere, in a help doc, a policy PDF, an FAQ page. Finding the right one takes time, and a normal chatbot is worse, because when it does not know the answer it just makes one up.

ProofRAG is my attempt at fixing that. You give it company documents. It answers questions only from those documents, and it shows the source with every answer. If the answer is not in the documents, it says so, or passes the question to a human. It does not guess.

Status: Phase 1, Phase 2 and Phase 3 are done. Phase 4 is in progress. The pipeline has been moved out of the notebooks into a proper Python package, and the improvement experiments are finished: every change was measured on the same fixed test set before it was allowed to stay. What is left in Phase 4 is the production work: the agent graph, the API, the database and the deployment.

## The problem in numbers

Knowledge workers spend about 1.8 hours a day just looking for information inside their own company (McKinsey). Support teams feel the same problem from the other side, the same basic questions arriving every day. A system that answers from verified documents, with sources, attacks both sides of it.

## How it works

Documents come in as help pages in markdown (PDF support comes later). They get split into small chunks, turned into embeddings, and stored in a vector store. Each chunk is also indexed under a few questions that the chunk can answer, generated when the index is built. Users ask in their own words, and a question matches a question far better than it matches a paragraph, so this lifts a lot of casually worded questions that plain chunk search used to miss. When a generated question matches, the system pulls in the real chunk behind it, so the model always reads the document, never the generated question.

When someone asks something, the system searches. A score threshold stops weak matches before they reach the model. If the best score is too low, the system first tries correcting the spelling of the question and searches once more, because a single typo can drag a good question's score from 0.59 down to 0.13. The language model then answers using only the picked chunks. After the answer is generated, a second check makes sure the answer is actually supported by the chunks. If the check fails, the model retries once with a stricter instruction. If it still fails, or confidence is low, the question gets flagged for a human instead of being sent out as it is.

The notebooks also had conversation memory, hybrid search (meaning based search plus BM25 keyword search), a cross encoder reranker, and multi query expansion. Phase 3 measured all of it, and on my data the plain semantic search beat every fancier variant, so semantic search is what the packaged system runs. The rest stays in the notebooks as experiments, with their numbers. Conversation memory comes back later in Phase 4, as part of the agent graph.

Right now the corpus is 25 Notion help articles, kept on my machine only, because they are Notion's content and not mine to redistribute. The code is public, the data is not. The generated questions file is in the repo, so the index can be rebuilt exactly without calling an API again.

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

The threshold analysis was the most useful part of this round. The no-answer questions are not all low scoring. The most dangerous ones, like which AI model Notion AI uses (score 0.63) and the exact price of the Plus plan (0.56), score higher than plenty of good questions, and they already pass the threshold today. The prompt and the verification check are what actually catch them. The threshold mostly blocks good questions asked in casual words. From the score data, lowering the threshold from 0.45 to 0.30 would let 14 more answerable questions through, and the no-answer questions it would newly let through are ones the prompt has already shown it can refuse at even higher scores. Two good questions score 0.14 and 0.15 though, below any sensible line. Those need a different fix, indexing the chunks in question form (FAQ style).

I also tested showing the model 5 chunks instead of 3. Retrieval improved by exactly one question, 83 out of 89, but the answer test told the real story: the extra chunks halved the model's own refusals, from 13 down to 6, and fully correct answers rose from 55 to 60. Five chunks stayed.

### The improvement round (final configuration)

Four changes were then tested one at a time, in this order: 5 chunks per question, the threshold lowered from 0.45 to 0.30 (tested first on just the 22 questions that score between the two lines: 9 recovered, and all 8 newly exposed no-answer questions still refused safely), a rewritten answer prompt that tells the model the answer may be worded differently or spread across chunks, and FAQ style indexing (2,065 generated questions over 689 chunks, tested first on the 10 worst questions before being rolled out to the whole index).

The final configuration was run on the full 104 questions twice, once on each of two different models, because a system that only works on one model is a weaker claim than one that works on two.

On Groq (openai/gpt-oss-120b): 75 answers fully correct, 3 partly correct, 11 refused even though the answer existed. That is 84% of the answerable questions answered fully correctly, up from 55 at the start of Phase 4. Of the 80 questions it did answer, not one was wrong, the 3 imperfect ones were incomplete rather than false.

On Gemini (gemini-3.5-flash-lite, a much smaller model): 72 fully correct, 1 partly correct, 16 refused. Same system, same settings, a lighter model, and it still held up.

On both models, all 15 no-answer questions were handled safely and zero answers were invented. On Groq, two of the 15 got a grounded "no" instead of a plain refusal (for example, PayPal is not among the payment methods the documents list), and the other 13 were refused outright.

What is still weak, honestly:

- Three questions score below any usable threshold (0.15 to 0.28). Their answers are split across two places in an article, so no single chunk matches them well. That is a chunking and document problem, not a model problem, and no setting I tried fixes it.
- One question (how to search for a page) failed three different ways across three runs: answered once, refused once, and once its answer failed the verification check. The models are not fully deterministic, and borderline questions show it.
- The generated FAQ questions vary in quality. One question the small pilot lifted cleanly did not lift in the full index, where it competes with 2,700 other entries.
- Latency and cost per question are still not measured. That is missing and I am not going to pretend otherwise.

## Build phases

Phase 1. Basic pipeline. Load documents, chunk them, store embeddings, retrieve, answer. **Done.**
Phase 2. Better retrieval. Hybrid search, reranking, conversation memory, self verification, one advanced trick (multi query) with measurements. **Done.**
Phase 3. Evaluation. A fixed set of 100 questions, checked for correct answers and correct sources. **Done.**
Phase 4. Production layer. **In progress.** The pipeline is packaged and the improvement round is done (results above). Next: rebuild the pipeline as an agent graph with LangGraph, which can retry a refused question with different wording before escalating it and brings conversation memory back, then FastAPI backend, Docker, AWS deployment (S3 for documents, PostgreSQL with pgvector on RDS for vectors and app data), guardrails, audit logs, tests, CI.
Phase 5. Finish. Architecture diagram, live demo, demo video.

## Tech used so far

Python, LangChain, FAISS (local vector store), BM25 for keyword search, MiniLM embeddings, a cross encoder reranker, Groq running openai/gpt-oss-120b as the main language model, Gemini (gemini-3.5-flash-lite) used as a second model for experiments and cross-checking, Streamlit for a small test UI. Phase 4 moves the vectors to PostgreSQL with pgvector on AWS RDS.

## Data source

- Notion Help Center

## Honest notes

This is not finished. What is measured is written above, including the parts that went badly. I would rather show real results late than invent good looking ones early.

One loose end from earlier is now closed: the corpus folder always had 25 clean files. The extra chunks I saw came from an old saved index, and re-running ingestion fixed it.

The known weakness is still over-refusal, but it shrank: from 31 out of 89 answerable questions at the start of Phase 4 to 11 in the final configuration. The improvement round is closed now. Whatever is left is written above as known limits, and the remaining planned gain is the retry loop inside the agent graph, not more tuning.

Evaluation runs on free API tiers, which have real daily limits. The Groq free tier allows 200,000 tokens a day, and on 23 Nov the day's test runs used up the whole budget and one test had to stop at its first question and wait for the next day. Experiments were moved to Gemini's free tier because its limit is per request count, which suits test runs better, and the final configuration was then verified on Groq. Free tiers have real limits. Measuring cost properly is still on my list, and this is exactly why it matters.

Built by Sahil Saeid, learning in public.
