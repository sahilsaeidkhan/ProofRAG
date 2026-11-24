import sys, time, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval import search
from src.pipeline import ask
from src.config import THRESHOLD

print("THRESHOLD in config:", THRESHOLD)

data = json.load(open("evaluation/golden_set_v3.json", encoding="utf-8"))
band = []
for item in data:
    results = search(item["question"])
    best = results[0][1] if results else 0.0
    if 0.30 <= best < 0.45:
        band.append((item, best))
print(f"Band questions: {len(band)}")

with open("evaluation/gate_band_result.txt", "w", encoding="utf-8") as f:
    for item, best in band:
        for attempt in range(5):
            try:
                r = ask(item["question"])
                break
            except Exception as e:
                if ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)) and attempt < 4:
                    print("Rate limit - 45s ruk raha hoon...")
                    time.sleep(45)
                else:
                    raise
        kind = "ANSWERABLE" if item["expected_source"] else "UNANSWERABLE"
        line = f"[{kind}] {item['question'][:70]} | score {best:.2f} | status {r['status']}"
        print(line)
        f.write(line + "\n")
        f.write("   A: " + r["answer"][:300].replace("\n", " ") + "\n")
        f.flush()
        time.sleep(2)
print("Done - evaluation/gate_band_result.txt")