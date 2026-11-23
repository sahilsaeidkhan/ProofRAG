import json
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import TOP_K
from src.retrieval import search
from src.pipeline import ask

GOLDEN = Path(__file__).parent / "golden_set_v3.json"
data = json.loads(GOLDEN.read_text(encoding="utf-8"))

hits = total = 0
unans = []
for item in data:
    results = search(item["question"], k=TOP_K)
    files = [d.metadata.get("file", "") for d, s in results]
    if item["expected_source"] is None:
        if results:
            unans.append(round(float(results[0][1]), 2))
    else:
        total += 1
        if item["expected_source"] in files:
            hits += 1
print(f"Retrieval (k={TOP_K}): {hits}/{total} hits")
print("Unanswerable best scores:", unans)

outfile = Path(__file__).parent / f"answer_eval_v3_k{TOP_K}.txt"
done_text = outfile.read_text(encoding="utf-8") if outfile.exists() else ""
start_from = done_text.count("expected:")
print(f"Already done: {start_from} — resuming from Q{start_from + 1}")

counts = {}
start = time.time()
for i, item in enumerate(data, 1):
    if i <= start_from:
        continue
    for attempt in range(5):
        try:
            r = ask(item["question"])
            break
        except Exception as e:
            if "429" in str(e) and attempt < 4:
                print(f"\nRate limit at Q{i} — 45s ruk raha hoon...")
                time.sleep(45)
            else:
                raise
    counts[r["status"]] = counts.get(r["status"], 0) + 1
    entry = (f"Q{i} [{item['type']}] {item['question']}\n"
             f"  expected: {item['expected_source']} | status: {r['status']} | score: {r['best_score']:.2f} | corrected: {r['corrected_question']}\n"
             f"  A: {r['answer']}\n")
    with outfile.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")
    print(f"{i}/{len(data)}", end="\r")
    time.sleep(2)
print(f"\nThis run: {counts} in {time.time() - start:.0f}s")
print("Appended to:", outfile)

