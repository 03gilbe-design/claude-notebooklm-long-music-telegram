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
                          ContextTypes, MessageHandler, filters)

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
    "Questa è la parte {i} di {n} di una serie. Inizia dicendo esattamente: "
    "'Questa è la parte {i} di {n}: si parla di {tema}'. "
    "Tratta SOLO questo tema: {tema}. "
    "Niente sigla iniziale né saluti finali lunghi: entra dritto nel contenuto."
    "{marker}{extra}"
)
# marker instruction added to the prompt only for hybrid/host modes
MARKER_ISTR = (
    " Inoltre: quando cambi sotto-argomento o vuoi un momento musicale, "
    "pronuncia da solo, chiaramente, esattamente la parola 'STACCO MUSICALE', poi continua."
)

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
    q = (f"Dividi l'argomento '{topic}' in esattamente {n} macro-temi per una serie di podcast, "
         f"in ordine logico. Rispondi SOLO con {n} righe, una per tema, senza numeri né altro.")
    r = cli(["ask", "-n", nb_id, q], timeout=600)
    testo = r.get("answer") or ""
    temi = [re.sub(r"^[\d\.\-\*\s]+", "", riga).strip() for riga in str(testo).splitlines() if riga.strip()]
    temi = [t for t in temi if 3 < len(t) < 200][:n]
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
        [B("➖", callback_data="n-"), B(f"🎙 {s['n']} episodes", callback_data="noop"), B("➕", callback_data="n+")],
        [B("🌐 Search: DEEP (complete)" if s["deep"] else "⚡ Search: FAST", callback_data="mode")],
        [B(f"✏️ Prompt: {s['extra_nome'] or 'standard'}", callback_data="p_menu")],
        [B(f"🎵 Music ({n_musica} types)" if n_musica else "🎵 Music (none in jingles/)", callback_data="mus_menu")],
        [B(f"📓 Notebook: {s.get('nb_nome') or 'new'}", callback_data="nb_menu")],
        [B("▶️ GO!", callback_data="go"), B("🏠 Menu", callback_data="m_home")],
    ])


def txt_pannello(ud):
    s = ud["setup"]
    t = (10 if s["deep"] else 4) + s["n"] * 8
    topic = ud['topic'] if len(ud['topic']) <= 100 else ud['topic'][:100] + "…"  # no wall of text
    return (f"🎬 {topic}\n\nAdjust and press ▶️ GO!\n⏱ estimated: ~{t}-{t + 15} min")


def kb_prompt_menu():
    righe = [[B("📝 Create new prompt", callback_data="p_nuovo")],
             [B("🔙 Use standard", callback_data="p_std")]]
    for i, c in enumerate(carica_custom()[:6]):
        righe.append([B(f"⭐ {c['nome'][:35]}", callback_data=f"p_prev:{i}"),
                      B("🗑", callback_data=f"p_del:{i}")])
    righe.append([B("↩️ Back", callback_data="p_back")])
    return KB(righe)


# ---------- handlers ----------

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙️ PodcastLab!\nWrite a topic (e.g., history of rome) or use the menu 👇")
    await menu(update, ctx)


async def testo_libero(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    attesa = ctx.user_data.get("attesa")
    if attesa == "prompt_testo":
        ctx.user_data["nuovo_prompt"] = testo
        ctx.user_data["attesa"] = "prompt_nome"
        await update.message.reply_text("👍 Now give it a short name (e.g., 'ironic style'):")
        return
    if attesa == "prompt_nome":
        lista = carica_custom()
        lista.insert(0, {"nome": testo[:50], "testo": ctx.user_data.pop("nuovo_prompt")})
        salva_custom(lista[:20])
        ctx.user_data["attesa"] = None
        s = ctx.user_data.setdefault("setup", setup_default())
        s["extra"] = " Also: " + lista[0]["testo"]
        s["extra_nome"] = lista[0]["nome"]
        if ctx.user_data.get("topic"):
            await update.message.reply_text(txt_pannello(ctx.user_data), reply_markup=kb_pannello(s))
        else:
            await update.message.reply_text("⭐ Saved and selected! Now write the podcast topic.")
        return
    if attesa == "topic":
        ctx.user_data["attesa"] = None
    if len(testo) < 3:
        await update.message.reply_text("Topic too short 🙂")
        return
    ctx.user_data["topic"] = testo
    s = ctx.user_data.setdefault("setup", setup_default())
    await update.message.reply_chat_action(ChatAction.TYPING)
    await update.message.reply_text(txt_pannello(ctx.user_data), reply_markup=kb_pannello(s))


async def bottoni(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ud = ctx.user_data
    s = ud.setdefault("setup", setup_default())
    d = q.data
    chat = update.effective_chat

    # --- main menu (ALWAYS works, even after bot restart) ---
    if d == "m_home":
        await q.edit_message_text("🎙️ PodcastLab — what do we do?", reply_markup=kb_menu())
        return
    if d == "m_nuovo":
        ud["attesa"] = "topic"
        await q.edit_message_text("🎬 Write the podcast topic (e.g., history of rome) 👇")
        return
    if d == "m_vecchi":
        # show COMPLETE podcasts (_UNITO); if a merge failed, fallback to singles
        uniti = sorted(OUT.glob("*_UNITO.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]
        mp3s = uniti or sorted(OUT.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]
        if not mp3s:
            await q.edit_message_text("📼 No podcast yet!", reply_markup=kb_menu())
            return
        righe = [[B(f"🎧 {f.stem.replace('_UNITO','')[:45]}", callback_data=f"v_send:{f.name[:55]}")] for f in mp3s]
        righe.append([B("🏠 Menu", callback_data="m_home")])
        await q.edit_message_text("📼 Tap to listen again:", reply_markup=KB(righe))
        return
    if d.startswith("v_send:"):
        nome = d[7:]
        matches = [f for f in OUT.glob("*.mp3") if f.name.startswith(nome[:50])]
        if matches and matches[0].stat().st_size >= 49 * 1024 * 1024:
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
            await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s))
        else:
            await q.edit_message_text("🎙️ PodcastLab — what do we do?", reply_markup=kb_menu())
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
        testo = f"🗂 {len(mp3s)} mp3 on PC.\n"
        testo += f"⏳ In progress: {lav}" if lav else "No work in progress."
        await q.edit_message_text(testo, reply_markup=kb_menu())
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
            "🎵 Choose the music (put more files in jingles/ to have options):",
            reply_markup=kb_musica(s))
        return
    if d.startswith("mus:"):  # mus:categoria:nomefile
        _, cat, nome = d.split(":", 2)
        s.setdefault("musica", {})[cat] = nome
        await q.edit_message_text("🎵 Choose the music:", reply_markup=kb_musica(s))
        return
    if d == "mus_back":
        await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s))
        return

    # --- menu prompt ---
    if d == "p_menu":
        await q.edit_message_text("✏️ Prompt for hosts:", reply_markup=kb_prompt_menu())
        return
    if d == "p_std":
        s["extra"], s["extra_nome"] = "", ""
    elif d == "p_nuovo":
        ud["attesa"] = "prompt_testo"
        await q.edit_message_text(
            "📝 Write me extra instructions for the hosts, free text.\n\n"
            "Examples:\n• «ironic tone, practical examples, simple explanation»\n"
            "• «college professor style, cite sources»\n"
            "• «fast pace, rhetorical questions»\n\nWrite and send 👇")
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
            await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s))
        else:
            await q.edit_message_text("⭐ Selected! Write the podcast topic 👇")
        return
    if not ud.get("topic"):
        await q.edit_message_text("🎙️ PodcastLab — what do we do?", reply_markup=kb_menu())
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
                righe.append([B(f"📓 {nome}", callback_data=f"nb_use:{nid}")])
        righe.append([B("↩️ Back", callback_data="nb_back")])
        await q.edit_message_text("📓 Notebook: create new or reuse existing sources?", reply_markup=KB(righe))
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
        await q.edit_message_text(f"🚀 Here we go: {ud['topic']}")
        await esegui(chat, ctx)
        return
    await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s))


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

    def avvisa(frac, testo):
        asyncio.run_coroutine_threadsafe(
            msg.edit_text(f"🔬 {topic} — {n} episodes\n\n{bar(frac)} {testo}"), loop)
        asyncio.run_coroutine_threadsafe(chat.send_chat_action(ChatAction.RECORD_VOICE), loop)

    def lavoro():
        if s.get("nb_id"):  # reuse existing notebook: sources already there, skip research
            nb_id = s["nb_id"]
            avvisa(0.25, f"Existing notebook 📓 🧩 Dividing into {n} macro-themes…")
            return _genera(nb_id)
        nb = cli(["create", topic[:80]])
        nb_id = nb.get("id") or nb.get("notebook", {}).get("id")
        if not nb_id:
            return f"Cannot create the notebook 😞 Try again shortly.\n(detail: {nb})"
        r = cli(["source", "add-research", "-n", nb_id, topic, "--mode", "deep" if deep else "fast"],
                timeout=3600)
        if r.get("error"):
            return f"Web search did not start 😞\n(detail: {r})"
        avvisa(0.15, "Phase 1/3: reading and choosing sources…")
        w = cli(["research", "wait", "-n", nb_id, "--import-all", "--timeout", "1800"], timeout=2000)
        if w.get("error"):
            return f"Web search failed or too slow 😞\n(detail: {w})"
        avvisa(0.25, f"Sources OK! 🧩 Dividing into {n} macro-themes…")
        return _genera(nb_id)

    def _genera(nb_id):
        temi = macro_temi(nb_id, topic, n)
        files = []
        for i, tema in enumerate(temi, 1):
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
            mp3 = OUT / f"{base}_parte{i}.mp3"
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
    temi_txt = "\n".join(f"  {i}. {t}" for i, t in enumerate(result["temi"], 1))
    await msg.edit_text(f"🎉 {topic} ready!\n\n{bar(1)} 100%\n\n📚 Episodes:\n{temi_txt}")
    for i, (f, tema) in enumerate(result["files"], 1):
        if f.exists() and f.stat().st_size > 1000:
            await chat.send_chat_action(ChatAction.UPLOAD_VOICE)
            await chat.send_audio(audio=open(f, "rb"), title=f"Part {i}: {tema[:50]}",
                                  caption=f"🎙 Part {i}/{len(result['files'])} — {tema}")
    u = result["unito"]
    if u and u.exists() and u.stat().st_size < 49 * 1024 * 1024:
        await chat.send_chat_action(ChatAction.UPLOAD_VOICE)
        await chat.send_audio(audio=open(u, "rb"), title=f"{topic} — COMPLETE",
                              caption="🎧 All episodes in one file")
    elif u:
        await chat.send_message(f"ℹ️ The merged file exceeds 50MB: it's on the PC in {u}")
    await chat.send_message("🎧 Happy listening!", reply_markup=kb_menu())


async def test_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Button test:", reply_markup=KB([[B("👍 Works!", callback_data="noop")]]))


async def on_error(update, ctx):
    log.error("Handler error: %s", ctx.error, exc_info=ctx.error)
    try:
        if update and update.effective_chat:
            await update.effective_chat.send_message(
                f"⚠️ Oops: {str(ctx.error)[:200]}", reply_markup=kb_menu())
    except Exception:
        pass


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("test", test_btn))
    app.add_handler(CallbackQueryHandler(bottoni))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, testo_libero))
    app.add_error_handler(on_error)
    log.info("PodcastLab bot started (v4 menu)")
    app.run_polling()


if __name__ == "__main__":
    main()
