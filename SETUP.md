# PodcastLab — avvio

## Cosa fa
`/podcast <topic>` su Telegram → deep research NotebookLM → 3 parti podcast con marker vocali → mp3 sul telefono. Poi Colab trascrive (word-level + chi parla) e `postprod.py` inserisce jingle ai marker.

## Setup (una volta, in ordine)
1. **Auth NotebookLM** (interattivo, fallo tu):
   ```
   notebooklm login
   ```
   (apre browser, login Google, salva auth di profilo — i vecchi storage_state in Downloads sono scaduti)
2. **Bot Telegram**: BotFather → `/newbot` → copia token → crea `C:\podcastlab\.env`:
   ```
   TELEGRAM_TOKEN=123456:ABC...
   N_PARTI=3
   ```
3. **Dipendenze**: `pip install python-telegram-bot` (notebooklm-py già installato). Serve `ffmpeg` nel PATH.
4. **Jingle**: metti mp3 in `C:\podcastlab\jingles\` (`intro.mp3` = sigla iniziale, qualsiasi altro = stacco). Clip video estratte in `C:\podcastlab\clips\`.
5. **Avvio automatico** (PowerShell admin):
   ```powershell
   schtasks /create /tn PodcastLabBot /tr "pythonw C:\podcastlab\bot.py" /sc onlogon /rl limited
   ```

## Flusso completo
1. Telefono: `/podcast storia di roma` → arrivano N mp3 grezzi.
2. GPU: apri `PodcastLab_Colab.ipynb` su Colab (T4), carica gli mp3 in Drive `PodcastLab/in`, run → JSON in `PodcastLab/out` (token HF nei Secrets Colab, nome `HF_TOKEN`).
3. PC: scarica i JSON accanto agli mp3, poi:
   ```
   python postprod.py out\topic_parte1.mp3 parte1.json out\topic_parte2.mp3 parte2.json -o finale.mp3
   ```
   → jingle al posto di ogni "STACCO MUSICALE" detto dagli host, clip al posto di "CLIP VIDEO", parti concatenate con intro.

## Sicurezza
- ⚠️ Token HF vecchio esposto in chiaro in `Downloads\GOOGLE_COLAB_chi_parla.ipynb` → **revocalo** su huggingface.co/settings/tokens.
- `storage_state*.json` in Downloads = login Google: scaduti ma da cestinare comunque.
- notebooklm-py usa cookie sessione = non ufficiale, ToS Google: modera la frequenza.
