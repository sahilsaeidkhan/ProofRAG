import sys, time, json, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_DIR
from src.ingestion import load_documents, split_documents
from src.generation import llm, _to_text

OUT = DATA_DIR / "faq_questions.json"
BATCH = 8
PER_CHUNK = 3

docs = load_documents()
chunks = split_documents(docs)
print(f"Chunks: {len(chunks)}")

if OUT.exists():
    all_questions = json.loads(OUT.read_text(encoding="utf-8"))
else:
    all_questions = [None] * len(chunks)
if len(all_questions) < len(chunks):
    all_questions += [None] * (len(chunks) - len(all_questions))

PROMPT = """For each numbered chunk below, write {n} short questions that the chunk answers.
Write the questions the way a user would ask them, in simple words.
Use this exact format and nothing else:
CHUNK 1:
- question
- question
- question
CHUNK 2:
- question
...

{body}"""


def parse(text, count):
    parts = re.split(r"CHUNK\s+(\d+)\s*:", text)
    found = {}
    it = iter(parts[1:])
    for num, body in zip(it, it):
        qs = [ln.strip()[2:].strip() for ln in body.splitlines() if ln.strip().startswith("- ")]
        found[int(num)] = [q for q in qs if q]
    return [found.get(i + 1, []) for i in range(count)]


for start in range(0, len(chunks), BATCH):
    batch = chunks[start:start + BATCH]
    if all(all_questions[start + j] is not None for j in range(len(batch))):
        continue
    body = "\n\n".join(f"CHUNK {j + 1}:\n{c.page_content}" for j, c in enumerate(batch))
    prompt = PROMPT.format(n=PER_CHUNK, body=body)
    for attempt in range(5):
        try:
            text = _to_text(llm.invoke(prompt))
            break
        except Exception as e:
            if ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)) and attempt < 4:
                print("Rate limit - 45s ruk raha hoon...")
                time.sleep(45)
            else:
                raise
    parsed = parse(text, len(batch))
    for j, qs in enumerate(parsed):
        all_questions[start + j] = qs
    OUT.write_text(json.dumps(all_questions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Done {min(start + BATCH, len(chunks))}/{len(chunks)}")
    time.sleep(2)

total = sum(len(q) for q in all_questions if q)
print(f"Saved {OUT} - total questions: {total}")