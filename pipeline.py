"""PodcastLab pipeline — links existing parts into a single command.

Does in order (each skips what is already done, so it resumes from where we were):
  1. download_audios.py     -> downloads audios from NotebookLM (auto-refresh auth)
  2. recover_prompts.py   -> recovers prompts (get-prompt)
  3. stato                -> tells what is still missing (transcriptions = on Colab GPU)

Does NOT redo anything: calls existing scripts. Transcription+dataset remains on
Colab (GPU) because locally it is too slow (PodcastLab_Colab.ipynb).

Usage: python pipeline.py          # downloads audio + prompt, then shows status
       python pipeline.py --stato  # only status, does not download
"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
AUDIO = BASE / "out" / "audio_notebooklm"
PROMPT = BASE / "out" / "prompts"


def step(nome, script):
    print(f"\n{'='*50}\n▶ {nome}\n{'='*50}")
    r = subprocess.run([sys.executable, str(BASE / script)], text=True)
    print(f"{'✅' if r.returncode == 0 else '⚠️'} {nome} finished (exit {r.returncode})")
    return r.returncode == 0


def stato():
    audio = list(AUDIO.glob("*.mp3")) if AUDIO.exists() else []
    prompt = list(PROMPT.glob("*.json")) if PROMPT.exists() else []
    print(f"\n{'='*50}\n📊 STATUS PodcastLab\n{'='*50}")
    print(f"🎧 audios downloaded:  {len(audio)}")
    print(f"📜 prompts recovered: {len(prompt)}")
    print("\n👉 Transcription+diarization+dataset: on Colab GPU (PodcastLab_Colab.ipynb).")
    print("   Upload out/audio_notebooklm and out/prompts to Drive, then run the notebook.")


def main():
    if "--stato" in sys.argv:
        stato()
        return
    step("1/2 Download audios from NotebookLM", "download_audios.py")
    step("2/2 Recover prompts", "recover_prompts.py")
    stato()


if __name__ == "__main__":
    main()
