"""Esegue il notebook Colab VERO in locale (CPU) con librerie VERE e audio VERO.

Does not mock transcription/diarization: runs faster-whisper + pyannote for real,
solo con google.colab stubbato (drive.mount -> cartella locale, userdata -> None).
Così testa il notebook end-to-end come su Colab, ma senza GPU/account.

Uso: python run_colab_local.py
Richiede: papermill, faster-whisper, pyannote.audio, soundfile already installed.
"""
import json
import os
import shutil
import site
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

NB = Path(r"C:\podcastlab\PodcastLab_Colab.ipynb")
REAL_AUDIO_DIR = Path(r"C:\podcastlab\out\audio_notebooklm")


def make_colab_shim(drive_root, secrets):
    """Crea un pacchetto google.colab finto in una dir che sta prima nel sys.path."""
    pkg = Path(tempfile.mkdtemp()) / "google" / "colab"
    pkg.mkdir(parents=True)
    (pkg.parent / "__init__.py").write_text("")
    (pkg / "__init__.py").write_text(
        "from . import drive, userdata\n")
    (pkg / "drive.py").write_text(
        f"def mount(path, **k):\n"
        f"    import os, pathlib\n"
        f"    # /content/drive già esiste come symlink/cartella verso la root locale\n"
        f"    print('drive.mount (shim) ->', {str(drive_root)!r})\n")
    (pkg / "userdata.py").write_text(
        "import json, os\n"
        f"_S = {json.dumps(secrets)}\n"
        "def get(k):\n"
        "    return _S.get(k)\n")
    return str(pkg.parent.parent)


def main():
    work = Path(tempfile.mkdtemp())
    # ricrea la struttura /content/drive/MyDrive che il notebook si aspetta
    mydrive = work / "content" / "drive" / "MyDrive"
    (mydrive / "PodcastLab").mkdir(parents=True)
    tr_mp3 = mydrive / "Trascrizioni_NotebookLM" / "mp3"
    tr_mp3.mkdir(parents=True)

    # metti 1 mp3 VERO breve (taglio 30s per test veloce su CPU)
    src = sorted(REAL_AUDIO_DIR.glob("*.mp3"))
    if not src:
        print("❌ nessun mp3 in", REAL_AUDIO_DIR); return 1
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src[0]),
                    "-t", "30", str(tr_mp3 / "test_reale.mp3")], check=True)
    print("audio di test:", (tr_mp3 / "test_reale.mp3").name, "(30s da", src[0].name + ")")

    # il notebook usa path assoluti /content/drive/... -> creo un symlink/junction
    content_link = Path("/content") if os.name != "nt" else None
    # su Windows non posso creare C:\content senza admin; invece PATCH il notebook
    # sostituendo /content/drive/MyDrive con la cartella work reale.
    nb = json.loads(NB.read_text(encoding="utf-8"))
    base_posix = str(mydrive).replace("\\", "/")
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            cell["source"] = [l.replace("/content/drive/MyDrive", base_posix) for l in cell["source"]]

    # cella 0 iniettata: stubba google.colab in sys.modules (batte il pacchetto google reale)
    shim_cell = {
        "cell_type": "code", "metadata": {}, "outputs": [], "execution_count": None,
        "source": [
            "import sys, types\n",
            "_c = types.ModuleType('google.colab')\n",
            "_d = types.ModuleType('google.colab.drive'); _d.mount = lambda *a, **k: print('drive.mount shim')\n",
            "_u = types.ModuleType('google.colab.userdata'); _u.get = lambda k: None\n",
            "_c.drive = _d; _c.userdata = _u\n",
            "import importlib\n",
            "try:\n",
            "    g = importlib.import_module('google')\n",
            "except Exception:\n",
            "    g = types.ModuleType('google'); sys.modules['google'] = g\n",
            "g.colab = _c\n",
            "sys.modules['google.colab'] = _c\n",
            "sys.modules['google.colab.drive'] = _d\n",
            "sys.modules['google.colab.userdata'] = _u\n",
            "print('✅ google.colab stubbato in locale')\n",
        ],
    }
    nb["cells"].insert(1, shim_cell)  # dopo il markdown(0), prima della CELLA 1

    patched = work / "nb_locale.ipynb"
    patched.write_text(json.dumps(nb), encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"

    print("\n=== ESEGUO IL NOTEBOOK VERO (papermill, CPU) ===")
    out = work / "nb_out.ipynb"
    r = subprocess.run([sys.executable, "-m", "papermill", str(patched), str(out),
                        "--log-output", "--no-progress-bar"],
                       env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(r.stdout[-3000:])
    if r.returncode != 0:
        print("--- STDERR ---\n", r.stderr[-2000:])
        print("\n❌ Notebook FALLITO — errore reale sopra.")
        return 1

    # verify it produced the transcript JSON
    outdir = mydrive / "PodcastLab" / "out"
    jsons = list(outdir.glob("*.json")) if outdir.exists() else []
    print(f"\n📄 JSON prodotti in PodcastLab/out: {len(jsons)}")
    for j in jsons:
        d = json.loads(j.read_text(encoding="utf-8"))
        voci = d.get("n_speaker", "?")
        txt = " ".join(s["text"] for s in d.get("segments", []))[:120]
        print(f"  {j.name}: {len(d.get('segments',[]))} seg, {voci} voci")
        print(f"    testo: {txt}…")
    print("\n✅ NOTEBOOK ESEGUITO END-TO-END IN LOCALE" if jsons else "\n⚠️ girato ma nessun JSON prodotto")
    return 0 if jsons else 1


if __name__ == "__main__":
    sys.exit(main())
