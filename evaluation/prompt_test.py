import sys, time, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import ask

data = json.load(open("evaluation/golden_set_v3.json", encoding="utf-8"))

targets = [10, 41, 46, 65, 80, 104, 12, 83, 85, 87, 48]
controls = [1, 5, 40, 45, 59, 67]
picked = []
for i, item in enumerate(data, start=1):
    if i in targets or i in controls or item["expected_source"] is None:
        picked.append((i, item))
print(f"Testing {len(picked)} questions")

with open("evaluation/prompt_test_result.txt", "w", encoding="utf-8") as f:
    for i, item in picked:
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
        line = f"Q{i} [{kind}] {item['question'][:70]} | status {r['status']}"
        print(line)
        f.write(line + "\n")
        f.write("   A: " + r["answer"][:300].replace("\n", " ") + "\n")
        f.flush()
        time.sleep(2)
print("Done - evaluation/prompt_test_result.txt")