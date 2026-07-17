---
name: notebooklm-podcast
description: Generate multi-part NotebookLM podcasts from a topic, transcribe & diarize them, and build a prompt+transcript dataset. Use when the user wants to turn a topic or sources into podcasts, download/transcribe NotebookLM audio overviews, recover the prompts used, add background music/stingers, or build a dataset of prompts and transcripts. Triggers on "notebooklm podcast", "audio overview", "generate podcast", "transcribe my podcasts", "podcast dataset".
---

# NotebookLM Podcast Skill

Drive the NotebookLM → podcast → dataset pipeline in this repo. It uses the unofficial
[`notebooklm-py`](https://github.com/teng-lin/notebooklm-py) API (pure HTTP after a one-time
browser login), plus `faster-whisper` (transcription) and `pyannote` (2-speaker diarization).

## Prerequisites (check first)

- `notebooklm login` has been run once (auth in `~/.notebooklm/profiles/default/storage_state.json`). If a command returns "Authentication expired", tell the user to run `notebooklm login` — it needs a browser and cannot be automated.
- `ffmpeg` in PATH. For transcription/diarization: a GPU (Colab T4) — CPU works but is slow.

## Common tasks

### Generate a podcast from a topic
Deep-research the topic on NotebookLM, then generate one or more audio overviews.
```bash
notebooklm create "TOPIC" --json                      # -> notebook id (in .notebook.id)
notebooklm source add-research -n <nb_id> "TOPIC" --mode deep --json
notebooklm research wait -n <nb_id> --import-all --json
notebooklm generate audio "custom prompt for the hosts" -n <nb_id> --length long --wait --json
# generate returns {task_id, status, url} — NOT artifact_id. Get it from the list:
notebooklm artifact list -n <nb_id> --json            # newest audio artifact -> its id
notebooklm download audio -n <nb_id> -a <artifact_id> out.mp3
```
Other output types (same command, free): `video`, `quiz`, `mind-map`, `flashcards`,
`slide-deck`, `infographic`, `data-table`, `report`.

### Recover the real prompt of an existing podcast
```bash
notebooklm artifact get-prompt <artifact_id> -n <nb_id> --json
```

### Get the extracted text/markdown of a source
```bash
notebooklm source fulltext <source_id> -n <nb_id> --format markdown -o source.md
```

### Batch download / transcribe / dataset
Use the repo scripts (each resumes, skipping what's already done):
- `python scarica_audio.py` — download all audio overviews
- `python recupera_prompt.py` — recover all prompts
- `PodcastLab_Colab.ipynb` on Colab GPU — transcribe + diarize (2 speakers) + build dataset

### Add music to a finished podcast
`postprod.py` inserts jingles from `jingles/` at spoken markers, or `bot.py`'s
`unisci_con_musica` puts intro/stinger/background at part boundaries (no transcription needed).

## Gotchas (verified)
- `generate audio` returns `task_id`+`url`, not `artifact_id` — always resolve the id via `artifact list`.
- `pyannote` 4.x cannot read mp3 directly (needs a waveform dict) and its output is `DiarizeOutput.speaker_diarization`, not a bare Annotation. Force `max_speakers=2` for NotebookLM podcasts (2 hosts).
- Auth `storage_state.json` expires ~24h; only `notebooklm login` (browser) refreshes it.
