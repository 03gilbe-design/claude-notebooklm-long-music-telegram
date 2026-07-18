"""PodcastLab post-production: vocal markers -> jingle -> merge.

Usage:
  python postprod.py part1.mp3 part1.json [part2.mp3 part2.json ...] -o finale.mp3

The JSON is the word-level output of PodcastLab_Colab.ipynb (whisperx).
Recognized markers (words said by the hosts, instructed via prompt):
  STACCO-MUSICALE  -> inserts jingle from jingles/
  CLIP-VIDEO       -> inserts clip from clips/ (if present)
The parts are concatenated with intro.mp3 (if it exists in jingles/) at the beginning.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).parent
JINGLES = BASE / "jingles"
CLIPS = BASE / "clips"

MARKERS = {
    "stacco": re.compile(r"stacco[\s\-_]?musicale", re.I),
    "clip": re.compile(r"clip[\s\-_]?video", re.I),
}


def find_markers(words):
    """words: list {word, start, end}. Returns [(type, t_start, t_end)] of markers (even on 2 words)."""
    out = []
    for i, w in enumerate(words):
        pair = w["word"] + (words[i + 1]["word"] if i + 1 < len(words) else "")
        for kind, rx in MARKERS.items():
            if rx.search(w["word"]) or rx.search(pair):
                end = words[i + 1]["end"] if (i + 1 < len(words) and rx.search(pair) and not rx.search(w["word"])) else w["end"]
                if not out or out[-1][1] < w["start"] - 2:  # dedup close markers
                    out.append((kind, w["start"], end))
    return out


def flat_words(segments):
    return [w for s in segments for w in s.get("words", []) if "start" in w and "end" in w]


def ffmpeg(args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg error: {r.stderr[-1000:]}")


def pick(folder, kind):
    """First audio file in the folder for that type (jingle*.mp3 / clip*.mp3), None if missing."""
    if not folder.exists():
        return None
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in {".mp3", ".wav", ".m4a"})
    return files[0] if files else None


def cut(src, start, end, dst):
    args = ["-i", str(src), "-ss", f"{start:.2f}"]
    if end is not None:
        args += ["-to", f"{end:.2f}"]
    ffmpeg(args + ["-acodec", "libmp3lame", "-q:a", "4", str(dst)])


def process_part(mp3, seg_json, tmp, idx):
    """Cuts the part at markers and interleaves jingle/clip. Returns list of files to concatenate."""
    data = json.loads(Path(seg_json).read_text(encoding="utf-8"))
    words = flat_words(data["segments"])
    markers = find_markers(words)
    print(f"  {Path(mp3).name}: {len(markers)} markers found")
    pieces = []
    prev = 0.0
    for j, (kind, mstart, mend) in enumerate(markers):
        chunk = tmp / f"p{idx}_c{j}.mp3"
        cut(mp3, prev, mstart, chunk)  # cut BEFORE the marker: the spoken word disappears
        pieces.append(chunk)
        insert = pick(JINGLES if kind == "stacco" else CLIPS, kind)
        if insert:
            pieces.append(insert)
        prev = mend
    last = tmp / f"p{idx}_last.mp3"
    cut(mp3, prev, None, last)
    pieces.append(last)
    return pieces


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="mp3 json pairs in part order")
    ap.add_argument("-o", "--out", default="podcast_finale.mp3")
    a = ap.parse_args()
    if len(a.files) % 2:
        sys.exit("mp3 json pairs are needed")
    pairs = list(zip(a.files[::2], a.files[1::2]))

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        playlist = []
        intro = JINGLES / "intro.mp3"
        if intro.exists():
            playlist.append(intro)
        for i, (mp3, js) in enumerate(pairs):
            playlist += process_part(mp3, js, tmp, i)
            stacco = pick(JINGLES, "stacco")
            if stacco and i < len(pairs) - 1:
                playlist.append(stacco)  # jingle between one part and another
        lst = tmp / "list.txt"
        lst.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in playlist), encoding="utf-8")
        ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lst), "-acodec", "libmp3lame", "-q:a", "3", a.out])
    print("OK ->", a.out)


if __name__ == "__main__":
    main()
