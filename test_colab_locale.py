"""Testa le celle del notebook Colab in LOCALE (senza GPU/Colab reali).

Mocka google.colab, torch, faster_whisper, pyannote, numpy così le celle 1-2
girano a secco e vengono a galla NameError / variabili non definite / ordine sbagliato.
NON verifica la trascrizione vera (serve GPU), ma cattura gli errori strutturali.

Uso: python test_colab_locale.py [notebook.ipynb]
"""
import json
import sys
import types
from pathlib import Path
from unittest import mock

try:
    sys.stdout.reconfigure(encoding="utf-8")  # emoji/accenti su terminale Windows cp1252
except Exception:
    pass

NB = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\podcastlab\PodcastLab_Colab.ipynb")


def fake_module(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


def build_mocks(tmp):
    """Finti moduli Colab/ML che non crashano ma registrano le chiamate."""
    # google.colab
    drive = fake_module("google.colab.drive", mount=lambda *a, **k: None)
    userdata = fake_module("google.colab.userdata", get=lambda k: None)
    colab = fake_module("google.colab", drive=drive, userdata=userdata)
    google = fake_module("google", colab=colab)

    # torch: cuda spento (simula CPU) per esercitare quel ramo
    cuda = types.SimpleNamespace(is_available=lambda: False, empty_cache=lambda: None)
    torch = fake_module("torch", cuda=cuda, device=lambda x: x)

    # faster_whisper
    class FakeModel:
        def __init__(self, *a, **k): pass
        def transcribe(self, *a, **k):
            seg = types.SimpleNamespace(start=0.0, end=1.0, text="ciao", words=[
                types.SimpleNamespace(word="ciao", start=0.0, end=1.0)])
            info = types.SimpleNamespace(language="it")
            return [seg], info
    fw = fake_module("faster_whisper", WhisperModel=FakeModel,
                     BatchedInferencePipeline=lambda model=None: FakeModel())

    # pyannote.audio
    class FakePipe:
        @staticmethod
        def from_pretrained(*a, **k): return FakePipe()
        def to(self, d): return self
        def __call__(self, path):
            ann = mock.Mock()
            ann.itertracks = lambda yield_label=True: [
                (types.SimpleNamespace(start=0.0, end=1.0), None, "SPEAKER_00")]
            return ann
    pa = fake_module("pyannote.audio", Pipeline=FakePipe)
    pyannote = fake_module("pyannote", audio=pa)

    # nvidia.cudnn (per il fix path)
    cudnn = fake_module("nvidia.cudnn", __file__=str(tmp / "cudnn" / "__init__.py"))
    nvidia = fake_module("nvidia", cudnn=cudnn)

    return {
        "google": google, "google.colab": colab, "google.colab.drive": drive,
        "google.colab.userdata": userdata, "torch": torch,
        "faster_whisper": fw, "pyannote": pyannote, "pyannote.audio": pa,
        "nvidia": nvidia, "nvidia.cudnn": cudnn,
    }


def run():
    import tempfile, os
    nb = json.loads(NB.read_text(encoding="utf-8"))
    code_cells = [(''.join(c['source'])) for c in nb['cells'] if c['cell_type'] == 'code']

    tmp = Path(tempfile.mkdtemp())
    # struttura Drive finta con un mp3 e un md, così trova_audio() trova qualcosa
    base = tmp / "content/drive/MyDrive"
    (base / "PodcastLab/in").mkdir(parents=True, exist_ok=True)
    (base / "Trascrizioni_NotebookLM/mp3").mkdir(parents=True, exist_ok=True)
    (base / "Trascrizioni_NotebookLM/mp3/test_audio.mp3").write_bytes(b"x" * 2000)
    (tmp / "cudnn").mkdir(exist_ok=True)

    mocks = build_mocks(tmp)
    # reindirizza i path Drive del notebook verso la cartella temp
    def patch_paths(src):
        return src.replace("/content/drive/MyDrive", str(base).replace("\\", "/"))

    glb = {"__name__": "__main__"}
    ok = True
    with mock.patch.dict(sys.modules, mocks):
        # salta la CELLA 1 (fa pip install reale) — testiamo solo la logica delle celle 2 e 3
        for idx, src in enumerate(code_cells):
            if 'pip' in src and 'install' in src and idx == 0:
                print(f"CELLA {idx}: saltata (contiene pip install)")
                continue
            src = patch_paths(src)
            # neutralizza subprocess pip e SystemExit da 'account sbagliato' (in locale i path sono finti)
            try:
                exec(compile(src, f"<cella {idx}>", "exec"), glb)
                print(f"CELLA {idx}: ✅ eseguita senza errori strutturali")
            except SystemExit as e:
                print(f"CELLA {idx}: ⏹ SystemExit (atteso in alcuni casi): {e}")
            except Exception as e:
                ok = False
                import traceback
                print(f"CELLA {idx}: ❌ {type(e).__name__}: {e}")
                traceback.print_exc()
    print("\n" + ("✅ NESSUN errore strutturale (NameError/ordine)." if ok else "❌ Trovati errori sopra."))
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
