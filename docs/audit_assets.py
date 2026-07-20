"""Audit asset rules across all GIF-generating scripts.

Rules (root principles, not one-off fixes):
 R1  no inline base64 images (unmaintainable, hides 404 stubs)
 R2  no remote http(s) image URLs (fail silently in html2image)
 R3  referenced local files must exist and not be error stubs
 R4  one icon file per concept: same concept must not use different files
Exit code 1 if any violation.
"""
import re
import sys
from pathlib import Path

DOCS = Path(r"C:\podcastlab\docs")
SCRIPTS = sorted(DOCS.glob("mass_production/**/*.py")) + sorted(DOCS.glob("mass_production/*.py"))

# R4: files that must NOT be referenced because a canonical one exists
BANNED_ASSETS = {
    "notebooklm_icon.svg": "notebooklm_iconmark.svg (wordmark with text -> icon-only)",
    "podcast_icon.png": "waveform_icon.png (episodes are waveforms, user-chosen)",
}

violations = []
for script in set(SCRIPTS):
    text = script.read_text(encoding="utf-8", errors="replace")
    rel = script.name
    for m in re.finditer(r'''<img[^>]*\bsrc=(["'])(.*?)\1''', text):
        src = m.group(2)
        line = text[: m.start()].count("\n") + 1
        if src.startswith("data:"):
            violations.append(f"{rel}:{line} R1 inline base64")
        elif src.startswith("http"):
            violations.append(f"{rel}:{line} R2 remote URL: {src[:80]}")
        elif src.startswith("file:///"):
            p = Path(src[8:].replace("%20", " "))
            if not p.exists():
                violations.append(f"{rel}:{line} R3 missing file: {p}")
            elif p.stat().st_size < 100 or p.read_bytes()[:14] == b"404: Not Found":
                violations.append(f"{rel}:{line} R3 stub/broken file: {p}")
            elif p.name in BANNED_ASSETS:
                violations.append(f"{rel}:{line} R4 use {BANNED_ASSETS[p.name]} instead of {p.name}")

if violations:
    print(f"FAIL {len(violations)} violations:")
    for v in violations:
        print(" ", v)
    sys.exit(1)
print(f"OK {len(set(SCRIPTS))} scripts clean")
