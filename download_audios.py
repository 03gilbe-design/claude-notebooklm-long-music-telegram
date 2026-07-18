"""Download ALL NotebookLM Audio Overviews to your PC.

Output: C:\\podcastlab\\out\\audio_notebooklm\\<title>.mp3
Skips those already downloaded -> re-runnable. Then you upload the folder to Drive PodcastLab/in.
"""
import json
import subprocess
from pathlib import Path

OUT = Path(__file__).parent / "out" / "audio_notebooklm"
OUT.mkdir(parents=True, exist_ok=True)


def _run(args, timeout):
    r = subprocess.run(["notebooklm"] + args + ["--json"], capture_output=True, text=True,
                       encoding="utf-8", timeout=timeout)
    try:
        return json.loads(r.stdout.strip())
    except json.JSONDecodeError:
        return {"error": True, "raw": (r.stdout or "")[-200:]}


def cli(args, timeout=600):
    out = _run(args, timeout)
    if out.get("error") and "expired" in str(out.get("message", "")) + str(out.get("raw", "")):
        print("Auth expired: automatic renewal...")
        subprocess.run(["notebooklm", "login"], capture_output=True, text=True, timeout=180)
        out = _run(args, timeout)
    return out


def safe(s):
    return "".join(c for c in s if c.isalnum() or c in " _-").strip()[:80]


nbs = cli(["list"]).get("notebooks", [])
print(f"{len(nbs)} notebooks")
tot, fatti = 0, 0
for nb in nbs:
    arts = cli(["artifact", "list", "-n", nb["id"]]).get("artifacts", [])
    for a in arts:
        if a.get("type_id") != "audio" or a.get("status_id") != 3:
            continue
        tot += 1
        mp3 = OUT / f"{safe(a.get('title', a['id']))}.mp3"
        if mp3.exists() and mp3.stat().st_size > 1000:
            print("skip:", mp3.name)
            continue
        print("downloading:", mp3.name)
        cli(["download", "audio", "-n", nb["id"], "-a", a["id"], str(mp3)], timeout=1200)
        if mp3.exists() and mp3.stat().st_size > 1000:
            fatti += 1
        else:
            print("  FAILED:", mp3.name)
print(f"FINISHED: {fatti} downloaded now, {tot} total in {OUT}")
