"""PodcastLab Telegram bot v4 — full button menu.

/start or /menu = main menu: new podcast, old podcasts (listen again),
custom prompts (create/choose/delete), status.
Setup: see SETUP.md. Token in .env. Auth: `notebooklm login` once.
"""
import asyncio
import json
import logging
import os
import re
import subprocess
from pathlib import Path

from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as KB, Update
from telegram.constants import ChatAction
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, PicklePersistence, filters)

BASE = Path(__file__).parent
OUT = BASE / "out"
PROMPTS_DIR = OUT / "prompts"
CUSTOM_FILE = BASE / "prompt_personalizzati.json"
OUT.mkdir(exist_ok=True)
PROMPTS_DIR.mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("podcastlab")

# ponytail: 3-line .env parser, no need for python-dotenv
for line in (BASE / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

TOKEN = os.environ["TELEGRAM_TOKEN"]

PART_PROMPT = (
    "Questo episodio è la parte {i} di {n} di una serie continua, ma NON dirlo agli ascoltatori: "
    "gli host non devono MAI annunciare 'questa è la parte X' o numerare l'episodio a voce, "
    "come se stessero semplicemente continuando una conversazione naturale. "
    "Tratta SOLO questo tema: {tema}. "
    "Niente sigla iniziale né saluti finali lunghi: entra dritto nel contenuto."
    "{marker}{extra}"
)
# marker instruction added to the prompt only for hybrid/host modes
MARKER_ISTR = (
    " Inoltre: quando cambi sotto-argomento o vuoi un momento musicale, "
    "pronuncia da solo, chiaramente, esattamente la parola 'STACCO MUSICALE', poi continua."
)

# Telegram Bot API hard limit: 50MB for both sendAudio and sendDocument (standard API,
# not a local server) — confirmed via a real 413 "Request Entity Too Large" on a 63.7MB
# file. 49MB used throughout as a safety margin. Would need a self-hosted Bot API server
# (up to 2GB) to raise this; not worth the operational complexity for a personal bot.
TELEGRAM_MAX_BYTES = 49 * 1024 * 1024

BAR_LEN = 8


def bar(frac):
    fill = round(frac * BAR_LEN)
    return "▓" * fill + "░" * (BAR_LEN - fill)


def _run_cli(args, timeout):
    r = subprocess.run(["notebooklm"] + args + ["--json"], capture_output=True, text=True,
                       encoding="utf-8", timeout=timeout)
    try:
        return json.loads(r.stdout.strip())
    except json.JSONDecodeError:
        return {"error": True, "raw": (r.stdout or "")[-400:] + (r.stderr or "")[-400:]}


def cli(args, timeout=1800):
    out = _run_cli(args, timeout)
    # expired cookies? browser profile stays logged in -> `login` renews automatically, then retry
    if out.get("error") and "expired" in str(out.get("message", "")) + str(out.get("raw", "")):
        log.info("Auth expired: automatic renewal...")
        subprocess.run(["notebooklm", "login"], capture_output=True, text=True, timeout=180)
        out = _run_cli(args, timeout)
    return out


def macro_temi(nb_id, topic, n):
    # ask for a FULL, complete outline (not one-liners) since this becomes ONE continuous
    # podcast split into n parts — richer per-part outline -> longer, more substantial episodes
    q = (f"Dobbiamo creare UN UNICO podcast continuo sull'argomento '{topic}', diviso in esattamente "
         f"{n} parti consecutive che insieme coprono l'argomento per intero, senza ripetizioni tra le parti. "
         f"Scrivi prima un indice completo di TUTTI i sotto-argomenti rilevanti, poi raggruppali in "
         f"{n} blocchi consecutivi e coerenti (uno per parte, in ordine logico). "
         f"Per ogni blocco scrivi 2-4 frasi che elencano nel dettaglio TUTTI i sotto-punti da trattare "
         f"in quella parte, così ogni episodio ha contenuto sostanzioso. "
         f"Rispondi SOLO con i {n} blocchi separati dalla riga '---', senza numerazione né titoli.")
    r = cli(["ask", "-n", nb_id, q], timeout=600)
    testo = r.get("answer") or ""
    temi = [re.sub(r"^[\d\.\-\*\s]+", "", blocco).strip() for blocco in str(testo).split("---")]
    temi = [t for t in temi if len(t) > 10][:n]
    while len(temi) < n:
        temi.append(f"{topic} — in-depth {len(temi) + 1}")
    return temi


def unisci(files, dest):
    lst = dest.with_suffix(".txt")
    lst.write_text("\n".join(f"file '{f.resolve().as_posix()}'" for f in files), encoding="utf-8")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", str(lst), "-acodec", "libmp3lame", "-q:a", "3", str(dest)],
                       capture_output=True, text=True)
    lst.unlink(missing_ok=True)
    return r.returncode == 0 and dest.exists()


# --- music: short mp3s in jingles/. 3 modes driven by existing files:
#   jingles/intro.mp3     = intro theme (INTERRUPTS, at the beginning)
#   jingles/stacco*.mp3   = transition between episodes (INTERRUPTS)
#   jingles/sottofondo.mp3= loop music UNDER the hosts' voices (low volume)
#   present together = HYBRID. No transcription needed. ---
JINGLES = BASE / "jingles"
SOTTOFONDO_VOL = 0.18  # ponytail: background music volume; raise/lower if it covers/can't be heard

FREESOUND_KEY = os.environ.get("FREESOUND_API_KEY", "")

def freesound_cerca(query, n=5):
    """Text search on Freesound's free catalog. Returns [{'id','name','preview_url'}]."""
    import requests
    r = requests.get("https://freesound.org/apiv2/search/text/", params={
        "query": query, "token": FREESOUND_KEY, "page_size": n,
        "fields": "id,name,previews,duration"}, timeout=15)
    r.raise_for_status()
    return [{"id": h["id"], "name": h["name"][:40], "duration": round(h.get("duration", 0)),
             "preview_url": h["previews"]["preview-hq-mp3"]} for h in r.json().get("results", [])]


def youtube_cerca(query, n=5):
    """YouTube search — human picks from the list, nothing auto-downloaded here.
    Returns [{'id','title','duration'}]."""
    import yt_dlp
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{n}:{query}", download=False)
    return [{"id": e["id"], "title": (e.get("title") or "?")[:50], "duration": e.get("duration") or 0}
            for e in info.get("entries", []) if e.get("id")]


def youtube_scarica_audio(video_id, dest_mp3):
    """Downloads ONLY the exact video id the user picked, as mp3 to dest_mp3 (no extension)."""
    import yt_dlp
    opts = {"quiet": True, "no_warnings": True, "format": "bestaudio/best",
            "outtmpl": str(dest_mp3.with_suffix("")), "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "5"}]}
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])


def _opzioni(nome_prefix):
    """All sound options available for a category (intro/stacco/sottofondo)."""
    if not JINGLES.exists():
        return []
    return sorted(f for f in JINGLES.glob(f"{nome_prefix}*") if f.suffix.lower() in (".mp3", ".wav", ".m4a"))

def _jingle(nome_prefix, scelta=None):
    """Chosen file for the category; if choice=None uses the first available."""
    opts = _opzioni(nome_prefix)
    if scelta:
        for o in opts:
            if o.name == scelta:
                return o
    return opts[0] if opts else None


def _mix_sottofondo(voce, musica, dest):
    """Mixes an episode (voice) with looped background music at low volume. The music is
    shortened to the voice duration (duration=first). Returns True if ok."""
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                        "-i", str(voce), "-stream_loop", "-1", "-i", str(musica),
                        "-filter_complex",
                        f"[1:a]volume={SOTTOFONDO_VOL}[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[out]",
                        "-map", "[out]", "-acodec", "libmp3lame", "-q:a", "3", str(dest)],
                       capture_output=True, text=True)
    return r.returncode == 0 and dest.exists()


def unisci_con_musica(files, dest, scelta=None):
    """files=[Path]. Builds the complete podcast with music.
    choice = {'intro':filename, 'stacco':filename, 'sottofondo':filename} (from bot buttons),
    None for each = uses the first available option in jingles/.
    - sottofondo -> each episode mixed with music under the voice
    - intro/stacco -> placed at the boundaries between episodes"""
    scelta = scelta or {}
    intro = _jingle("intro", scelta.get("intro"))
    stacco = _jingle("stacco", scelta.get("stacco"))
    sotto = _jingle("sottofondo", scelta.get("sottofondo"))
    tmpdir = dest.parent
    episodes = [f for f in files if f.exists() and f.stat().st_size > 1000]
    if not episodes:
        return False

    # 1. if background music exists, mix each episode (voice + music under)
    lavorate = []
    for i, f in enumerate(episodes):
        if sotto:
            mixata = tmpdir / f"_mix_{i}_{f.name}"
            if _mix_sottofondo(f, sotto, mixata):
                lavorate.append(mixata)
            else:
                lavorate.append(f)  # if mix fails, use raw voice
        else:
            lavorate.append(f)

    # 2. final sequence with intro/stacco at the boundaries
    seq = ([intro] if intro else []) + []
    for i, f in enumerate(lavorate):
        seq.append(f)
        if stacco and i < len(lavorate) - 1:
            seq.append(stacco)

    inputs = []
    for f in seq:
        inputs += ["-i", str(f)]
    filtro = "".join(f"[{k}:a]" for k in range(len(seq))) + f"concat=n={len(seq)}:v=0:a=1[out]"
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs,
                        "-filter_complex", filtro, "-map", "[out]",
                        "-acodec", "libmp3lame", "-q:a", "3", str(dest)],
                       capture_output=True, text=True)
    for m in lavorate:  # clean up temporary mixes
        if m.name.startswith("_mix_"):
            m.unlink(missing_ok=True)
    return r.returncode == 0 and dest.exists()


def carica_custom():
    if CUSTOM_FILE.exists():
        try:
            return json.loads(CUSTOM_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def salva_custom(lista):
    CUSTOM_FILE.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")


def setup_default():
    return {"n": 3, "deep": True, "extra": "", "extra_nome": "", "modo": "noi",
            "nb_id": None, "nb_nome": "",
            "musica": {"intro": None, "stacco": None, "sottofondo": None}}

MODI = {"noi": "🎼 Just us (intro/outro/transitions)",
        "ibrido": "🎛 Hybrid (we + host signal)",
        "host": "🎙 Hosts decide (marker in speech)"}


def kb_musica(setup):
    """Menu to CHOOSE among sound options available in jingles/."""
    righe = []
    for cat, etichetta in (("intro", "🎬 Intro"), ("stacco", "🔔 Transition"), ("sottofondo", "🎵 Background")):
        opts = _opzioni(cat)
        scelto = setup.get("musica", {}).get(cat)
        if not opts:
            righe.append([B(f"{etichetta}: (no file — put them in jingles/)", callback_data="noop")])
            continue
        # chosen name (or "auto" = first option)
        nome_scelto = scelto or (opts[0].name if opts else "—")
        righe.append([B(f"{etichetta}: {nome_scelto[:28]}", callback_data="noop")])
        # a row of buttons for options (max 3 to avoid clutter)
        riga = []
        for o in opts[:4]:
            mark = "🔘" if o.name == nome_scelto else "▫️"
            riga.append(B(f"{mark} {o.stem.replace(cat+'_','').replace(cat,'')[:14] or 'default'}",
                          callback_data=f"mus:{cat}:{o.name[:40]}"))
        righe.append(riga)
    righe.append([B("🎬 Upload intro", callback_data="mus_up:intro"),
                  B("🔔 Upload transition", callback_data="mus_up:stacco")])
    righe.append([B("🎵 Upload background", callback_data="mus_up:sottofondo")])
    if FREESOUND_KEY:
        righe.append([B("🔎 Browse free catalog", callback_data="mus_cat"),
                      B("🤖 Auto (AI picks)", callback_data="mus_auto")])
    righe.append([B("▶️ Search YouTube", callback_data="mus_yt")])
    righe.append([B("↩️ Back", callback_data="mus_back")])
    return KB(righe)


# ---------- main menu ----------

def kb_menu():
    return KB([
        [B("🎬 New podcast", callback_data="m_nuovo")],
        [B("📼 My podcasts", callback_data="m_vecchi"),
         B("📜 My prompts", callback_data="m_prompt")],
        [B("ℹ️ Status", callback_data="m_stato"),
         B("❓ Help", callback_data="m_help")],
    ])


async def menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_message("🎙️ PodcastLab — what do we do?", reply_markup=kb_menu())


# ---------- new podcast panel ----------

def kb_pannello(s):
    n_musica = sum(1 for c in ("intro", "stacco", "sottofondo") if _opzioni(c))
    return KB([
        [B("➖ fewer", callback_data="n-"), B(f"🎙 {s['n']} episodes", callback_data="noop"), B("➕ more", callback_data="n+")],
        [B("🌐 Search: DEEP (complete)" if s["deep"] else "⚡ Search: FAST", callback_data="mode")],
        [B(f"✏️ Prompt: {s['extra_nome'] or 'default (no extra style)'}", callback_data="p_menu")],
        [B(f"🎵 Music ({n_musica} types)" if n_musica else "🎵 Music (none in jingles/)", callback_data="mus_menu")],
        [B(f"📓 Notebook: {s.get('nb_nome') or 'new'}", callback_data="nb_menu")],
        [B("▶️ GO!", callback_data="go"), B("ℹ️ Status", callback_data="m_stato")],
        [B("🏠 Menu", callback_data="m_home")],
    ])


def txt_pannello(ud):
    import html
    s = ud.setdefault("setup", setup_default())
    t = (10 if s["deep"] else 4) + s["n"] * 8
    # ud["topic"] can be missing if the bot restarted since this chat's last message
    # (in-memory session state, wiped on every deploy) — never crash, ask again instead
    topic_raw = ud.get("topic") or ""
    topic_raw = topic_raw if len(topic_raw) <= 100 else topic_raw[:100] + "…"  # no wall of text
    topic = html.escape(topic_raw)  # user-controlled text -> must escape before HTML parse_mode
    # Card layout (research: go-telegram/ui pattern) — bold header, monospace value, clear CTA footer
    return (f"<b>🎬 {topic}</b>\n\n"
            f"Adjust below, then press ▶️ GO!\n"
            f"⏱ Estimated time: <code>~{t}-{t + 15} min</code>")


PAGE_SIZE = 6

def kb_prompt_menu(page=0):
    tutti = carica_custom()
    lo = page * PAGE_SIZE
    righe = [[B("📝 Create new prompt", callback_data="p_nuovo")],
             [B("🔙 No extra style (default)", callback_data="p_std")]]
    for i, c in enumerate(tutti[lo:lo + PAGE_SIZE], start=lo):
        righe.append([B(f"📄 {c['nome'][:35]}", callback_data=f"p_prev:{i}"),
                      B("🗑", callback_data=f"p_del:{i}")])
    nav = []
    if page > 0:
        nav.append(B("⬅️ Prev", callback_data=f"p_page:{page-1}"))
    if lo + PAGE_SIZE < len(tutti):
        nav.append(B("➡️ Next", callback_data=f"p_page:{page+1}"))
    if nav:
        righe.append(nav)
    righe.append([B("↩️ Back", callback_data="p_back")])
    return KB(righe)


# ---------- handlers ----------

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙️ PodcastLab!\nWrite a topic (e.g., history of rome) or use the menu 👇")
    await menu(update, ctx)


async def audio_ricevuto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handles an audio/voice/document sent while attesa == upload_<categoria>."""
    attesa = ctx.user_data.get("attesa", "")
    if not attesa.startswith("upload_"):
        # orphaned audio: sent without going through Music -> Upload first — don't drop silently
        await update.message.reply_text(
            "🎧 Got your audio, but I don't know what to do with it.\n"
            "To use it as a jingle: Music menu → Upload intro/transition/background, then send it again.")
        return
    cat = attesa[len("upload_"):]
    ctx.user_data["attesa"] = None
    file_obj = update.message.audio or update.message.voice or update.message.document
    if not file_obj:
        await update.message.reply_text("⚠️ That's not an audio file. Try again from 🎵 Music.")
        return
    tg_file = await file_obj.get_file()
    ext = os.path.splitext(getattr(file_obj, "file_name", "") or "")[1].lower() or ".mp3"
    if ext not in (".mp3", ".wav", ".m4a"):
        ext = ".mp3"
    JINGLES.mkdir(exist_ok=True)
    n_esistenti = len(_opzioni(cat))
    dest = JINGLES / f"{cat}{'' if n_esistenti == 0 else '_' + str(n_esistenti + 1)}{ext}"
    await tg_file.download_to_drive(str(dest))
    s = ctx.user_data.setdefault("setup", setup_default())
    s.setdefault("musica", {})[cat] = dest.name
    etichette = {"intro": "🎬 intro", "stacco": "🔔 transition", "sottofondo": "🎵 background"}
    await update.message.reply_text(
        f"✅ Saved as {etichette[cat]} and selected: {dest.name}",
        reply_markup=kb_musica(s) if ctx.user_data.get("topic") else kb_menu())


async def testo_libero(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    attesa = ctx.user_data.get("attesa")
    if attesa and attesa.startswith("upload_"):
        # was expecting an audio file, got text instead — don't silently fall through to
        # the topic-setter below and overwrite their config
        await update.message.reply_text(
            "🎧 I'm waiting for an audio file, not text. Send the audio, or press Cancel above.")
        return
    if attesa and attesa.startswith("catsearch_"):
        cat = attesa[len("catsearch_"):]
        ctx.user_data["attesa"] = None
        try:
            hits = freesound_cerca(testo, n=5)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Search failed: {e}", reply_markup=kb_musica(
                ctx.user_data.setdefault("setup", setup_default())))
            return
        if not hits:
            await update.message.reply_text("😞 No results, try a different search.")
            return
        ctx.user_data["fs_results"] = {str(h["id"]): h for h in hits}
        righe = [[B(f"▶️ {h['name']} ({h['duration']}s)", callback_data=f"mus_pick:{cat}:{h['id']}")]
                 for h in hits]
        righe.append([B("↩️ Back", callback_data="mus_menu")])
        await update.message.reply_text("🔎 Pick one (free, Freesound.org):", reply_markup=KB(righe))
        return
    if attesa and attesa.startswith("ytsearch_"):
        cat = attesa[len("ytsearch_"):]
        ctx.user_data["attesa"] = None
        try:
            hits = youtube_cerca(testo, n=5)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Search failed: {e}", reply_markup=kb_musica(
                ctx.user_data.setdefault("setup", setup_default())))
            return
        if not hits:
            await update.message.reply_text("😞 No results, try a different search.")
            return
        ctx.user_data["yt_results"] = {h["id"]: h for h in hits}
        durata = lambda s: f"{s // 60}:{s % 60:02d}" if s else "?"
        righe = [[B(f"▶️ {h['title']} ({durata(h['duration'])})", callback_data=f"mus_ytpick:{cat}:{h['id']}")]
                 for h in hits]
        righe.append([B("↩️ Back", callback_data="mus_menu")])
        await update.message.reply_text("▶️ Pick one (downloads only this one):", reply_markup=KB(righe))
        return
    if attesa == "prompt_testo":
        ctx.user_data["nuovo_prompt"] = testo
        ctx.user_data["attesa"] = "prompt_nome"
        await update.message.reply_text("👍 Now give it a short name (e.g., 'ironic style'):")
        return
    if attesa == "prompt_nome":
        ctx.user_data["attesa"] = None
        nome, prompt_testo = testo[:50], ctx.user_data.pop("nuovo_prompt")
        ctx.user_data["nuovo_prompt_pending"] = {"nome": nome, "testo": prompt_testo}
        await update.message.reply_text(
            f"⭐ {nome}\n\n📜 {prompt_testo[:800]}\n\nSave this prompt?",
            reply_markup=KB([[B("✅ Save & use", callback_data="p_conferma"),
                              B("↩️ Discard", callback_data="p_scarta")]]))
        return
    if attesa == "topic":
        ctx.user_data["attesa"] = None
    if len(testo) < 3:
        await update.message.reply_text("Topic too short 🙂")
        return
    ctx.user_data["topic"] = testo
    s = ctx.user_data.setdefault("setup", setup_default())
    await update.message.reply_chat_action(ChatAction.TYPING)
    await update.message.reply_text(txt_pannello(ctx.user_data), reply_markup=kb_pannello(s), parse_mode="HTML")


async def bottoni(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ud = ctx.user_data
    s = ud.setdefault("setup", setup_default())
    d = q.data
    chat = update.effective_chat
    # any button click cancels a pending "waiting for free text" state (Cancel buttons rely
    # on this: branches below that need a fresh wait state set ud["attesa"] again explicitly)
    ud["attesa"] = None
    # a stale inline keyboard (from before the current podcast started) can still mutate
    # ud["setup"] mid-run and confuse the NEXT podcast's config — block everything except
    # read-only navigation while a job is active
    SAFE_WHILE_BUSY = {"m_home", "m_vecchi", "m_stato", "m_help"}
    SAFE_PREFIXES_WHILE_BUSY = ("v_send:", "m_vecchi_page:")
    if ud.get("lavoro_in_corso") and d not in SAFE_WHILE_BUSY and not d.startswith(SAFE_PREFIXES_WHILE_BUSY):
        # q.answer() already fired above (spinner-stop) — can't call it twice, so just ignore
        return

    # --- main menu (ALWAYS works, even after bot restart) ---
    if d == "m_home":
        await q.edit_message_text("<b>🎙️ PodcastLab</b>\nWhat do we do?", reply_markup=kb_menu(), parse_mode="HTML")
        return
    if d == "m_nuovo":
        ud["attesa"] = "topic"
        await q.edit_message_text("🎬 Write the podcast topic (e.g., history of rome) 👇")
        return
    if d == "m_vecchi" or d.startswith("m_vecchi_page:"):
        page = int(d.split(":")[1]) if ":" in d else 0
        # show COMPLETE podcasts (_UNITO); if a merge failed, fallback to singles
        uniti = sorted(OUT.glob("*_UNITO.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
        mp3s_all = uniti or sorted(OUT.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not mp3s_all:
            await q.edit_message_text("<b>📼 No podcast yet!</b>", reply_markup=kb_menu(), parse_mode="HTML")
            return
        lo = page * PAGE_SIZE
        mp3s = mp3s_all[lo:lo + PAGE_SIZE]
        righe = [[B(f"🎧 {f.stem.replace('_UNITO','')[:45]}", callback_data=f"v_send:{f.name[:55]}")] for f in mp3s]
        nav = []
        if page > 0:
            nav.append(B("⬅️ Prev", callback_data=f"m_vecchi_page:{page-1}"))
        if lo + PAGE_SIZE < len(mp3s_all):
            nav.append(B("➡️ Next", callback_data=f"m_vecchi_page:{page+1}"))
        if nav:
            righe.append(nav)
        righe.append([B("🏠 Menu", callback_data="m_home")])
        await q.edit_message_text(f"📼 Tap to listen again ({len(mp3s_all)} total):", reply_markup=KB(righe))
        return
    if d.startswith("v_send:"):
        nome = d[7:]
        matches = [f for f in OUT.glob("*.mp3") if f.name.startswith(nome[:50])]
        if matches and matches[0].stat().st_size >= TELEGRAM_MAX_BYTES:
            await chat.send_message(f"ℹ️ File too large for Telegram (>50MB). It's on the PC: {matches[0]}")
        elif matches:
            await chat.send_chat_action(ChatAction.UPLOAD_VOICE)
            await chat.send_audio(audio=open(matches[0], "rb"), title=matches[0].stem)
        else:
            await chat.send_message("⚠️ File not found on PC.")
        return
    if d == "m_prompt":
        await q.edit_message_text("✏️ Prompt for podcast hosts:", reply_markup=kb_prompt_menu())
        return
    if d == "p_back":
        if ud.get("topic"):
            await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s), parse_mode="HTML")
        else:
            await q.edit_message_text("<b>🎙️ PodcastLab</b>\nWhat do we do?", reply_markup=kb_menu(), parse_mode="HTML")
        return
    if d.startswith("p_prev:"):  # preview before choosing
        try:
            i = int(d.split(":")[1])
            c = carica_custom()[i]
            await q.edit_message_text(
                f"⭐ {c['nome']}\n\n📜 {c['testo'][:800]}",
                reply_markup=KB([[B("✅ Use this", callback_data=f"p_use:{i}"),
                                  B("↩️ Back", callback_data="p_menu2")]]))
        except (IndexError, ValueError):
            await q.edit_message_text("✏️ Prompt:", reply_markup=kb_prompt_menu())
        return
    if d == "p_menu2":
        await q.edit_message_text("✏️ Prompt for podcast hosts:", reply_markup=kb_prompt_menu())
        return
    if d == "m_stato":
        mp3s = sorted(OUT.glob("*.mp3"))
        lav = ud.get("lavoro_in_corso")
        testo = f"🗂 {len(mp3s)} audio files saved so far (episodes + merged podcasts).\n"
        testo += f"⏳ In progress: {lav}" if lav else "No work in progress."
        if ud.get("topic"):
            await q.edit_message_text(testo, reply_markup=KB([[B("↩️ Back", callback_data="p_menu2b")]]))
        else:
            await q.edit_message_text(testo, reply_markup=kb_menu())
        return
    if d == "p_menu2b":
        await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s), parse_mode="HTML")
        return
    if d == "m_help":
        await q.edit_message_text(
            "❓ How it works:\n"
            "1. Write any topic in chat\n"
            "2. Adjust episodes/search/prompt with buttons\n"
            "3. ▶️ GO! and wait: mp3s will arrive here\n\n"
            "📜 Custom prompts are saved and reused.\n"
            "📼 Old podcasts can be listened to from the menu.", reply_markup=kb_menu())
        return

    # --- music menu: choose among sound options ---
    if d == "mus_menu":
        await q.edit_message_text(
            "<b>🎵 Music</b>\nChoose below (put more files in jingles/ for options):",
            reply_markup=kb_musica(s), parse_mode="HTML")
        return
    if d.startswith("mus_up:"):  # ask for an audio upload for this category
        cat = d.split(":", 1)[1]
        ud["attesa"] = f"upload_{cat}"
        etichette = {"intro": "🎬 intro", "stacco": "🔔 transition", "sottofondo": "🎵 background"}
        await q.edit_message_text(
            f"📤 Send me the {etichette[cat]} audio file now (as a Telegram audio/voice/document).",
            reply_markup=KB([[B("↩️ Cancel", callback_data="mus_menu")]]))
        return
    if d.startswith("mus:"):  # mus:categoria:nomefile
        _, cat, nome = d.split(":", 2)
        s.setdefault("musica", {})[cat] = nome
        await q.edit_message_text("<b>🎵 Music</b>", reply_markup=kb_musica(s), parse_mode="HTML")
        return
    if d == "mus_auto":  # AI picks a jingle for all 3 categories, no user interaction
        # NOTE: no topic mixed in — Freesound tags are English/generic, foreign or
        # specific topic words (e.g. "storia di roma") kill the match entirely.
        # multiple query candidates per category: retry the next one if a search comes back empty
        queries = {"intro": ["upbeat podcast intro jingle", "podcast intro", "short jingle"],
                   "stacco": ["short transition sound effect", "whoosh transition", "swoosh"],
                   "sottofondo": ["soft background music loop", "ambient background music", "calm instrumental loop"]}
        await q.edit_message_text("🤖 Picking music for you…")
        salvati = []
        for cat, candidati in queries.items():
            hits, query = [], None
            for query in candidati:
                try:
                    hits = freesound_cerca(query, n=1)
                except Exception as e:
                    salvati.append(f"⚠️ {cat}: search failed ({e})")
                    hits = []
                    break
                if hits:
                    break
            if not hits:
                salvati.append(f"⚠️ {cat}: no result after {len(candidati)} tries")
                continue
            hit = hits[0]
            JINGLES.mkdir(exist_ok=True)
            n_esistenti = len(_opzioni(cat))
            dest = JINGLES / f"{cat}{'' if n_esistenti == 0 else '_' + str(n_esistenti + 1)}.mp3"
            import requests
            r = requests.get(hit["preview_url"], timeout=30)
            dest.write_bytes(r.content)
            s.setdefault("musica", {})[cat] = dest.name
            salvati.append(f"✅ {cat}: {hit['name']} ({hit['duration']}s)")
        await q.edit_message_text("🤖 Auto-picked:\n" + "\n".join(salvati), reply_markup=kb_musica(s))
        for cat in queries:
            dest = JINGLES / (s.get("musica", {}).get(cat) or "")
            if dest.exists():
                await chat.send_audio(audio=open(dest, "rb"), title=f"{cat} — preview")
        return
    if d == "mus_yt":  # pick a category to search YouTube for (human picks the result, nothing auto)
        await q.edit_message_text(
            "▶️ What category is this jingle for?",
            reply_markup=KB([[B("🎬 Intro", callback_data="mus_yt:intro"),
                              B("🔔 Transition", callback_data="mus_yt:stacco")],
                             [B("🎵 Background", callback_data="mus_yt:sottofondo")],
                             [B("↩️ Back", callback_data="mus_menu")]]))
        return
    if d.startswith("mus_yt:"):
        cat = d.split(":", 1)[1]
        ud["attesa"] = f"ytsearch_{cat}"
        await q.edit_message_text("▶️ Type a YouTube search (e.g. \"lofi background music no copyright\"):")
        return
    if d.startswith("mus_ytpick:"):  # mus_ytpick:categoria:video_id — downloads ONLY the id the user picked
        _, cat, vid = d.split(":", 2)
        risultati = ud.get("yt_results") or {}
        hit = risultati.get(vid)
        if not hit:
            await q.edit_message_text("⚠️ Search results expired, try again.", reply_markup=kb_musica(s))
            return
        await q.edit_message_text(f"⬇️ Downloading \"{hit['title']}\"…")
        JINGLES.mkdir(exist_ok=True)
        n_esistenti = len(_opzioni(cat))
        dest = JINGLES / f"{cat}{'' if n_esistenti == 0 else '_' + str(n_esistenti + 1)}.mp3"
        try:
            youtube_scarica_audio(vid, dest)
        except Exception as e:
            await q.edit_message_text(f"⚠️ Download failed: {e}", reply_markup=kb_musica(s))
            return
        s.setdefault("musica", {})[cat] = dest.name
        await q.edit_message_text(f"✅ Downloaded and selected: {dest.name}", reply_markup=kb_musica(s))
        await chat.send_audio(audio=open(dest, "rb"), title=f"{cat} — preview")
        return
    if d == "mus_cat":  # pick a category to browse the free catalog for
        await q.edit_message_text(
            "🔎 What category is this jingle for?",
            reply_markup=KB([[B("🎬 Intro", callback_data="mus_cat:intro"),
                              B("🔔 Transition", callback_data="mus_cat:stacco")],
                             [B("🎵 Background", callback_data="mus_cat:sottofondo")],
                             [B("↩️ Back", callback_data="mus_menu")]]))
        return
    if d.startswith("mus_cat:"):
        cat = d.split(":", 1)[1]
        ud["attesa"] = f"catsearch_{cat}"
        await q.edit_message_text("🔎 Type what kind of sound you're looking for (e.g. \"upbeat jingle\", \"soft piano\"):")
        return
    if d.startswith("mus_pick:"):  # mus_pick:categoria:freesound_id (URL looked up from last search, too long for callback_data)
        _, cat, fs_id = d.split(":", 2)
        risultati = ud.get("fs_results") or {}
        hit = risultati.get(fs_id)
        if not hit:
            await q.edit_message_text("⚠️ Search results expired, try again.", reply_markup=kb_musica(s))
            return
        JINGLES.mkdir(exist_ok=True)
        n_esistenti = len(_opzioni(cat))
        dest = JINGLES / f"{cat}{'' if n_esistenti == 0 else '_' + str(n_esistenti + 1)}.mp3"
        import requests
        r = requests.get(hit["preview_url"], timeout=30)
        dest.write_bytes(r.content)
        s.setdefault("musica", {})[cat] = dest.name
        await q.edit_message_text(f"✅ Downloaded and selected: {dest.name}", reply_markup=kb_musica(s))
        await chat.send_audio(audio=open(dest, "rb"), title=f"{cat} — preview")
        return
    if d == "mus_back":
        await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s), parse_mode="HTML")
        return

    # --- menu prompt ---
    if d == "p_menu":
        await q.edit_message_text("<b>✏️ Prompt for hosts</b>", reply_markup=kb_prompt_menu(), parse_mode="HTML")
        return
    if d.startswith("p_page:"):
        await q.edit_message_text("<b>✏️ Prompt for hosts</b>", reply_markup=kb_prompt_menu(int(d.split(":")[1])), parse_mode="HTML")
        return
    if d in ("p_conferma", "p_scarta"):
        pending = ud.pop("nuovo_prompt_pending", None)
        if d == "p_conferma" and pending:
            lista = carica_custom()
            lista.insert(0, pending)
            salva_custom(lista[:20])
            s["extra"], s["extra_nome"] = " Also: " + pending["testo"], pending["nome"]
        if ud.get("topic"):
            await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s), parse_mode="HTML")
        else:
            await q.edit_message_text(
                "⭐ Saved and selected! Now write the podcast topic." if d == "p_conferma" else "Discarded.",
                reply_markup=kb_menu())
        return
    if d == "p_std":
        s["extra"], s["extra_nome"] = "", ""
    elif d == "p_nuovo":
        ud["attesa"] = "prompt_testo"
        await q.edit_message_text(
            "📝 Write me extra instructions for the hosts, free text.\n\n"
            "Examples:\n• «ironic tone, practical examples, simple explanation»\n"
            "• «college professor style, cite sources»\n"
            "• «fast pace, rhetorical questions»\n\nWrite and send 👇",
            reply_markup=KB([[B("↩️ Cancel", callback_data="p_menu")]]))
        return
    elif d.startswith("p_use:"):
        try:
            c = carica_custom()[int(d.split(":")[1])]
            s["extra"], s["extra_nome"] = " Also: " + c["testo"], c["nome"]
        except IndexError:
            pass
    elif d.startswith("p_del:"):
        lista = carica_custom()
        try:
            rimosso = lista.pop(int(d.split(":")[1]))
            salva_custom(lista)
            if s["extra_nome"] == rimosso["nome"]:
                s["extra"], s["extra_nome"] = "", ""
        except IndexError:
            pass
        await q.edit_message_text("🗑 Deleted.", reply_markup=kb_prompt_menu())
        return

    # --- new podcast panel ---
    if d in ("p_std",) or d.startswith("p_use:"):
        if ud.get("topic"):
            await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s), parse_mode="HTML")
        else:
            await q.edit_message_text("⭐ Selected! Write the podcast topic 👇")
        return
    if not ud.get("topic"):
        await q.edit_message_text("<b>🎙️ PodcastLab</b>\nWhat do we do?", reply_markup=kb_menu(), parse_mode="HTML")
        return
    if d == "noop":
        return
    if d == "n+":
        s["n"] = min(8, s["n"] + 1)
    elif d == "n-":
        s["n"] = max(1, s["n"] - 1)
    elif d == "mode":
        s["deep"] = not s["deep"]
    elif d == "nb_menu":
        r = cli(["list"])  # cli() auto-renews expired cookies once
        if r.get("error"):
            await q.edit_message_text(
                "🍪 NotebookLM cookies expired and auto-renewal failed 😞\n"
                "Run `notebooklm login` on the PC, then press 📓 again.",
                reply_markup=kb_pannello(s))
            return
        nbs = (r.get("notebooks") or [])[:8]
        righe = [[B("🆕 New notebook", callback_data="nb_new")]]
        for nb_ in nbs:
            nid, nome = nb_.get("id"), (nb_.get("title") or nb_.get("id") or "?")[:35]
            if nid:
                righe.append([B(f"📓 {nome}", callback_data=f"nb_prev:{nid}")])
        righe.append([B("↩️ Back", callback_data="nb_back")])
        await q.edit_message_text("📓 Notebook: create new or reuse existing sources?", reply_markup=KB(righe))
        return
    elif d.startswith("nb_prev:"):  # preview: title + sources before confirming
        nid = d.split(":", 1)[1]
        titolo = next(((n_.get("title") or "?") for n_ in (cli(["list"]).get("notebooks") or [])
                       if n_.get("id") == nid), "?")
        fonti = (cli(["source", "list", "-n", nid], timeout=120).get("sources") or [])
        elenco = "\n".join(f"• {(f_.get('title') or f_.get('name') or '?')[:60]}" for f_ in fonti[:8])
        extra_f = f"\n…+{len(fonti) - 8} more" if len(fonti) > 8 else ""
        await q.edit_message_text(
            f"📓 {titolo}\n\n📚 {len(fonti)} sources:\n{elenco or '(none)'}{extra_f}",
            reply_markup=KB([[B("✅ Use this", callback_data=f"nb_use:{nid}"),
                              B("↩️ Back", callback_data="nb_menu")]]))
        return
    elif d in ("nb_new", "nb_back"):
        if d == "nb_new":
            s["nb_id"], s["nb_nome"] = None, ""
    elif d.startswith("nb_use:"):
        s["nb_id"] = d.split(":", 1)[1]
        s["nb_nome"] = next((( n_.get("title") or "?")[:20] for n_ in (cli(["list"]).get("notebooks") or [])
                             if n_.get("id") == s["nb_id"]), "existing")
    elif d == "go":
        if ud.get("lavoro_in_corso"):  # block double-start (spam GO / second topic)
            await q.answer("⚠️ A podcast is already being processed!", show_alert=True)
            return
        # set the lock BEFORE the next await — a double-click can interleave here and both
        # pass the check above before either sets the lock, launching 2 parallel jobs
        ud["lavoro_in_corso"] = ud["topic"]
        await q.edit_message_text(f"🚀 Here we go: {ud['topic']}")
        await esegui(chat, ctx)
        return
    await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s), parse_mode="HTML")


def slug(testo):
    """Safe filename on Windows/Drive: no \\/:*?\"<>| and spaces->_."""
    return re.sub(r'[\\/*?:"<>|]', '', testo[:40]).replace(' ', '_').strip('_') or "podcast"


async def esegui(chat, ctx):
    ud = ctx.user_data
    topic, s = ud["topic"], ud["setup"]
    n, deep, extra = s["n"], s["deep"], s["extra"]
    marker = MARKER_ISTR if s.get("modo") in ("ibrido", "host") else ""  # hosts signal only in hybrid/host
    ud["lavoro_in_corso"] = topic
    base = slug(topic)
    msg = await chat.send_message(
        f"🔬 {topic} — {n} episodes ({'deep' if deep else 'fast'})\n\n"
        f"{bar(0.05)} Phase 1/3: searching for sources on the web…\n(I'll write to you: you can close Telegram)")
    loop = asyncio.get_running_loop()
    import time
    t_start = time.time()
    TIMING_LOG = BASE / "timing_dataset.jsonl"

    def avvisa(frac, testo):
        asyncio.run_coroutine_threadsafe(
            msg.edit_text(f"🔬 {topic} — {n} episodes\n\n{bar(frac)} {testo}"), loop)
        asyncio.run_coroutine_threadsafe(chat.send_chat_action(ChatAction.RECORD_VOICE), loop)
        # phase-timing dataset: lets future runs show real ETAs instead of a fixed guess
        try:
            with open(TIMING_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": time.time(), "elapsed_s": round(time.time() - t_start, 1),
                                    "topic": topic, "n_episodes": n, "deep": deep,
                                    "frac": frac, "fase": testo}, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def lavoro():
        if s.get("nb_id"):  # reuse existing notebook: sources already there, skip research
            nb_id = s["nb_id"]
            avvisa(0.25, f"Existing notebook 📓 🧩 Dividing into {n} macro-themes…")
            return _genera(nb_id)
        nb = cli(["create", topic[:80]])
        nb_id = nb.get("id") or nb.get("notebook", {}).get("id")
        if not nb_id:
            return f"Cannot create the notebook 😞 Try again shortly.\n(detail: {nb})"
        r = cli(["source", "add-research", "-n", nb_id, topic, "--mode", "deep" if deep else "fast", "--no-wait"],
                timeout=60)
        if r.get("error"):
            return f"Web search did not start 😞\n(detail: {r})"
        # live progress: poll status ourselves instead of blocking on 'research wait' —
        # shows the real source count as it grows, not just a frozen "searching..." message
        import time
        deadline = time.time() + 1800
        n_fonti_prev = -1
        while time.time() < deadline:
            st = cli(["research", "status", "-n", nb_id], timeout=60)
            n_fonti = len(st.get("sources") or [])
            stato = st.get("status", "?")
            if n_fonti != n_fonti_prev:
                avvisa(0.10 + min(0.10, n_fonti * 0.01),
                      f"Phase 1/3: reading and choosing sources… ({n_fonti} found, {stato})")
                n_fonti_prev = n_fonti
            if stato == "completed":
                break
            if stato == "error":
                return f"Web search failed 😞\n(detail: {st})"
            time.sleep(4)
        w = cli(["research", "wait", "-n", nb_id, "--import-all", "--timeout", "300"], timeout=400)
        if w.get("error"):
            return f"Web search failed or too slow 😞\n(detail: {w})"
        avvisa(0.25, f"Sources OK! 🧩 Dividing into {n} macro-themes…")
        return _genera(nb_id)

    def _genera(nb_id):
        temi = macro_temi(nb_id, topic, n)
        files = []
        for i, tema in enumerate(temi, 1):
            mp3 = OUT / f"{base}_parte{i}.mp3"
            if mp3.exists() and mp3.stat().st_size > 1000:
                # resume: this episode was already generated (e.g. a previous run got
                # interrupted) — don't waste time/NotebookLM quota regenerating it
                tema_precedente = tema
                pj = PROMPTS_DIR / f"{mp3.stem}.json"
                if pj.exists():
                    try:
                        tema_precedente = json.loads(pj.read_text(encoding="utf-8")).get("tema", tema)
                    except Exception:
                        pass
                avvisa(0.25 + 0.65 * (i - 1) / n, f"Phase 2/3: 🎙 episode {i}/{n} — already done, skipping")
                files.append((mp3, tema_precedente))
                continue
            avvisa(0.25 + 0.65 * (i - 1) / n, f"Phase 2/3: 🎙 episode {i}/{n}\n{tema}")
            prompt = PART_PROMPT.format(i=i, n=n, tema=tema, marker=marker, extra=extra)
            g = cli(["generate", "audio", prompt, "-n", nb_id,
                     "--length", "long", "--wait", "--timeout", "1800"], timeout=2000)
            # generate returns {task_id, status, url}, NOT artifact_id -> I get it from artifact list
            art_id = g.get("artifact_id") or g.get("id")
            if not art_id and g.get("status") == "completed":
                audio = [a for a in cli(["artifact", "list", "-n", nb_id]).get("artifacts", [])
                         if a.get("type_id") == "audio" and a.get("status_id") == 3]
                audio.sort(key=lambda a: a.get("created_at", ""), reverse=True)
                art_id = audio[0]["id"] if audio else None
            if not art_id:
                return f"Episode {i} ({tema}) failed 😞\n(detail: {g})"
            cli(["download", "audio", "-n", nb_id, "-a", art_id, str(mp3)])
            (PROMPTS_DIR / f"{mp3.stem}.json").write_text(json.dumps(
                {"topic": topic, "parte": i, "tema": tema, "prompt": prompt,
                 "notebook_id": nb_id, "artifact_id": art_id}, ensure_ascii=False, indent=1),
                encoding="utf-8")
            files.append((mp3, tema))
            cli(["artifact", "delete", art_id, "-n", nb_id])  # 1 audio/notebook -> free up slot
        avvisa(0.95, "Phase 3/3: 🎵 merging episodes + intro and transitions…")
        unito = OUT / f"{base}_UNITO.mp3"
        ok = unisci_con_musica([f for f, _ in files], unito, s.get("musica"))
        return {"files": files, "unito": unito if ok else None, "temi": temi}

    def _genera_un_episodio(nb_id, i, tema):
        """One episode's generate+download+cleanup, safe to run concurrently with others
        IF NotebookLM's 'generate audio' response reliably includes artifact_id directly
        (the common path below) — the list-sorted-by-latest fallback is NOT concurrency-safe
        (race: two episodes finishing close together could grab each other's artifact) and
        is only expected to trigger rarely. UNTESTED under real concurrent load as of writing —
        validate with a real NotebookLM run (2-3 episodes truly parallel) before trusting it."""
        mp3 = OUT / f"{base}_parte{i}.mp3"
        if mp3.exists() and mp3.stat().st_size > 1000:
            tema_precedente = tema
            pj = PROMPTS_DIR / f"{mp3.stem}.json"
            if pj.exists():
                try:
                    tema_precedente = json.loads(pj.read_text(encoding="utf-8")).get("tema", tema)
                except Exception:
                    pass
            return (mp3, tema_precedente)
        prompt = PART_PROMPT.format(i=i, n=n, tema=tema, marker=marker, extra=extra)
        g = cli(["generate", "audio", prompt, "-n", nb_id,
                 "--length", "long", "--wait", "--timeout", "1800"], timeout=2000)
        art_id = g.get("artifact_id") or g.get("id")
        if not art_id:
            raise RuntimeError(f"Episode {i} ({tema}) failed: no artifact_id in response (detail: {g})")
        cli(["download", "audio", "-n", nb_id, "-a", art_id, str(mp3)])
        (PROMPTS_DIR / f"{mp3.stem}.json").write_text(json.dumps(
            {"topic": topic, "parte": i, "tema": tema, "prompt": prompt,
             "notebook_id": nb_id, "artifact_id": art_id}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        cli(["artifact", "delete", art_id, "-n", nb_id])
        return (mp3, tema)

    def _genera_parallela(nb_id):
        """DRAFT, not wired in yet. Runs all n episodes concurrently via threads instead of
        sequentially. Only use once validated for real against the NotebookLM API."""
        import concurrent.futures
        temi = macro_temi(nb_id, topic, n)
        avvisa(0.25, f"Phase 2/3: 🎙 generating all {n} episodes in parallel…")
        with concurrent.futures.ThreadPoolExecutor(max_workers=n) as ex:
            futures = [ex.submit(_genera_un_episodio, nb_id, i, tema) for i, tema in enumerate(temi, 1)]
            files = [f.result() for f in futures]  # raises if any episode failed
        avvisa(0.95, "Phase 3/3: 🎵 merging episodes + intro and transitions…")
        unito = OUT / f"{base}_UNITO.mp3"
        ok = unisci_con_musica([f for f, _ in files], unito, s.get("musica"))
        return {"files": files, "unito": unito if ok else None, "temi": temi}

    try:
        result = await asyncio.to_thread(lavoro)
    except Exception as e:
        ud["lavoro_in_corso"] = None  # secure the lock: if lavoro() crashes, it doesn't hang
        await msg.edit_text(f"❌ Unexpected error: {str(e)[:200]}")
        await chat.send_message("🏠 Menu:", reply_markup=kb_menu())
        return
    ud["lavoro_in_corso"] = None
    if isinstance(result, str):
        await msg.edit_text(f"❌ {result}")
        await chat.send_message("🏠 Menu:", reply_markup=kb_menu())
        return
    import html as _html
    temi_txt = "\n".join(f"  {i}. {_html.escape(t)}" for i, t in enumerate(result["temi"], 1))
    await msg.edit_text(
        f"<b>🎉 {_html.escape(topic)} ready!</b>\n\n<code>{bar(1)} 100%</code>\n\n<b>📚 Episodes:</b>\n{temi_txt}",
        parse_mode="HTML")
    for i, (f, tema) in enumerate(result["files"], 1):
        if f.exists() and f.stat().st_size > 1000:
            await chat.send_chat_action(ChatAction.UPLOAD_VOICE)
            await chat.send_audio(audio=open(f, "rb"), title=f"Part {i}: {tema[:50]}",
                                  caption=f"🎙 Part {i}/{len(result['files'])} — {tema}")
    u = result["unito"]
    if u and u.exists() and u.stat().st_size >= TELEGRAM_MAX_BYTES:
        # too big for Telegram (50MB hard limit) — recompress at a lower bitrate instead
        # of just telling the user it's stuck on the PC
        compresso = u.with_stem(u.stem + "_compressed")
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(u), "-b:a", "96k", str(compresso)],
                           capture_output=True, text=True)
        if r.returncode == 0 and compresso.exists() and compresso.stat().st_size < TELEGRAM_MAX_BYTES:
            u = compresso
        else:
            u = None
            await chat.send_message(f"ℹ️ The merged file is too large even compressed: it's on the PC in {result['unito']}")
    if u and u.exists() and u.stat().st_size < TELEGRAM_MAX_BYTES:
        await chat.send_chat_action(ChatAction.UPLOAD_VOICE)
        await chat.send_audio(audio=open(u, "rb"), title=f"{topic} — COMPLETE",
                              caption="🎧 All episodes in one file")
    await chat.send_message("🎧 Happy listening! What next?", reply_markup=KB([
        [B("🎬 New podcast", callback_data="m_nuovo")],
        [B("📼 My podcasts", callback_data="m_vecchi"), B("🏠 Menu", callback_data="m_home")]]))


async def test_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Button test:", reply_markup=KB([[B("👍 Works!", callback_data="noop")]]))


async def on_error(update, ctx):
    # re-clicking a button that leads to the SAME screen: Telegram rejects the
    # no-op edit. Content on screen is already correct -> just ack, don't bounce to menu.
    if "Message is not modified" in str(ctx.error):
        try:
            if update and update.callback_query:
                await update.callback_query.answer()
        except Exception:
            pass
        return
    log.error("Handler error: %s", ctx.error, exc_info=ctx.error)
    try:
        if update and update.effective_chat:
            await update.effective_chat.send_message(
                f"⚠️ Oops: {str(ctx.error)[:200]}", reply_markup=kb_menu())
    except Exception:
        pass


def main():
    # persists ctx.user_data to disk so a bot restart (frequent during deploys) doesn't
    # wipe the topic/setup a user was mid-way through configuring
    persistence = PicklePersistence(filepath=str(BASE / "bot_session.pickle"))
    app = Application.builder().token(TOKEN).persistence(persistence).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("test", test_btn))
    app.add_handler(CallbackQueryHandler(bottoni))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.AUDIO, audio_ricevuto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, testo_libero))
    app.add_error_handler(on_error)
    log.info("PodcastLab bot started (v4 menu)")
    app.run_polling()


if __name__ == "__main__":
    main()
