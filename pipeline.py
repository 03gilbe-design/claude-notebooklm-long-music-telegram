"""PodcastLab pipeline — lega i pezzi già esistenti in un comando unico.

Fa in fila (ognuno salta ciò che è già fatto, quindi riprende da dove eravamo):
  1. scarica_audio.py     -> scarica gli audio da NotebookLM (auto-refresh auth)
  2. recupera_prompt.py   -> recupera i prompt (get-prompt)
  3. stato                -> dice cosa manca ancora (trascrizioni = su Colab GPU)

NON rifà niente: chiama gli script che ci sono già. La trascrizione+dataset resta su
Colab (GPU) perché in locale è troppo lento (PodcastLab_Colab.ipynb).

Uso:  python pipeline.py          # scarica audio + prompt, poi mostra stato
      python pipeline.py --stato  # solo lo stato, non scarica
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
    print(f"{'✅' if r.returncode == 0 else '⚠️'} {nome} finito (exit {r.returncode})")
    return r.returncode == 0


def stato():
    audio = list(AUDIO.glob("*.mp3")) if AUDIO.exists() else []
    prompt = list(PROMPT.glob("*.json")) if PROMPT.exists() else []
    print(f"\n{'='*50}\n📊 STATO PodcastLab\n{'='*50}")
    print(f"🎧 audio scaricati:  {len(audio)}")
    print(f"📜 prompt recuperati: {len(prompt)}")
    print("\n👉 Trascrizione+diarizzazione+dataset: su Colab GPU (PodcastLab_Colab.ipynb).")
    print("   Carica out/audio_notebooklm e out/prompts su Drive, poi lancia il notebook.")


def main():
    if "--stato" in sys.argv:
        stato()
        return
    step("1/2 Scarico audio da NotebookLM", "scarica_audio.py")
    step("2/2 Recupero i prompt", "recupera_prompt.py")
    stato()


if __name__ == "__main__":
    main()
