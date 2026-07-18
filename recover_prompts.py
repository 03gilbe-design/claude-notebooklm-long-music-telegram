"""Recover the TRUE prompts of all Audio Overviews (verb artifact get-prompt, not chat).

Output: C:\\podcastlab\\out\\prompts\\<title>.json  {notebook, title, prompt, links, artifact_id}
Skips those already saved -> re-runnable whenever you want.
"""
import json
import subprocess
from pathlib import Path

OUT = Path(__file__).parent / "out" / "prompts"
OUT.mkdir(parents=True, exist_ok=True)


def cli(args, timeout=300):
    r = subprocess.run(["notebooklm"] + args + ["--json"], capture_output=True, text=True,
                       encoding="utf-8", timeout=timeout)
    try:
        return json.loads(r.stdout.strip())
    except json.JSONDecodeError:
        return {"error": True, "raw": (r.stdout + r.stderr)[-300:]}


def safe(s):
    return "".join(c for c in s if c.isalnum() or c in " _-").strip()[:80]


nbs = cli(["list"]).get("notebooks", [])
print(f"{len(nbs)} notebooks found")
for nb in nbs:
    nb_id, nb_title = nb["id"], nb.get("title", "?")
    arts = cli(["artifact", "list", "-n", nb_id]).get("artifacts", [])
    audio = [a for a in arts if a.get("type_id") == "audio"]
    if not audio:
        continue
    links = None  # lazy: sources downloaded only if at least one new artifact is needed
    for a in audio:
        out = OUT / f"{safe(a.get('title', a['id']))}.json"
        if out.exists():
            print("  skip:", out.name)
            continue
        if links is None:
            src = cli(["source", "list", "-n", nb_id]).get("sources", [])
            links = [s.get("uri") or s.get("title") for s in src]
        p = cli(["artifact", "get-prompt", a["id"], "-n", nb_id])
        prompt = p.get("prompt")
        out.write_text(json.dumps({
            "notebook": nb_title, "title": a.get("title"), "artifact_id": a["id"],
            "notebook_id": nb_id, "prompt": prompt, "links": links,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {out.name}  prompt={'YES' if prompt else 'EMPTY'}")
print("FINISHED ->", OUT)
