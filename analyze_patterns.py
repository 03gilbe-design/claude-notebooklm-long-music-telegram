"""Pattern analysis over prompts generated so far (out/prompts/*.json).
Transcript-side pattern analysis (repeated phrases in the actual audio) needs a
transcription step first (Colab whisper pipeline, not run locally by design) —
not possible yet, no transcript data exists in this project.
"""
import json
import re
from collections import Counter
from pathlib import Path

PROMPTS_DIR = Path(r"C:\podcastlab\out\prompts")

def main():
    files = list(PROMPTS_DIR.glob("*.json"))
    temi, topics, prompt_lens = [], [], []
    word_counter = Counter()
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        temi.append(d.get("tema", ""))
        topics.append(d.get("topic", ""))
        prompt_lens.append(len(d.get("prompt") or ""))
        for w in re.findall(r"[a-zà-ù]{4,}", (d.get("tema") or "").lower()):
            word_counter[w] += 1

    print(f"Prompt totali analizzati: {len(files)}")
    print(f"Topic distinti: {len(set(topics))}")
    print(f"Lunghezza media prompt: {sum(prompt_lens)//max(1,len(prompt_lens))} caratteri")
    print(f"\nParole più ricorrenti nei temi (>=4 lettere, escluse comuni):")
    stopwords = {"della", "delle", "degli", "questo", "questa", "sono", "come", "loro",
                "anche", "quando", "dove", "quali", "sulla", "nella", "alla", "quale"}
    for w, n in word_counter.most_common(30):
        if w not in stopwords and n > 2:
            print(f"  {n:3d}  {w}")

if __name__ == "__main__":
    main()
