"""PodcastLab bot Telegram v4 — menu completo a bottoni.

/start o /menu = menu principale: nuovo podcast, vecchi podcast (riascolta),
prompt personalizzati (crea/scegli/cancella), stato.
Setup: vedi AVVIO.md. Token in .env. Auth: `notebooklm login` una volta.
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

# ponytail: .env parser 3 righe, python-dotenv non serve
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
# istruzione marker aggiunta al prompt solo per le modalità ibrido/host
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
    # cookie scaduti? il profilo browser resta loggato -> `login` rinnova da solo, poi riprova
    if out.get("error") and "expired" in str(out.get("message", "")) + str(out.get("raw", "")):
        log.info("Auth scaduta: rinnovo automatico...")
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
        temi.append(f"{topic} — approfondimento {len(temi) + 1}")
    return temi


def unisci(files, dest):
    lst = dest.with_suffix(".txt")
    lst.write_text("\n".join(f"file '{f.resolve().as_posix()}'" for f in files), encoding="utf-8")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", str(lst), "-acodec", "libmp3lame", "-q:a", "3", str(dest)],
                       capture_output=True, text=True)
    lst.unlink(missing_ok=True)
    return r.returncode == 0 and dest.exists()


# --- musica: mp3 corti in jingles/. 3 modalità guidate dai file presenti:
#   jingles/intro.mp3     = sigla iniziale (INTERROMPE, all'inizio)
#   jingles/stacco*.mp3   = stacco tra le puntate (INTERROMPE)
#   jingles/sottofondo.mp3= musica loop SOTTO la voce degli host (basso volume)
#   presenti insieme = IBRIDO. Nessuna trascrizione serve. ---
JINGLES = BASE / "jingles"
SOTTOFONDO_VOL = 0.18  # ponytail: volume musica di sottofondo; alza/abbassa se copre/non si sente

def _opzioni(nome_prefix):
    """Tutte le opzioni sonore disponibili per una categoria (intro/stacco/sottofondo)."""
    if not JINGLES.exists():
        return []
    return sorted(f for f in JINGLES.glob(f"{nome_prefix}*") if f.suffix.lower() in (".mp3", ".wav", ".m4a"))

def _jingle(nome_prefix, scelta=None):
    """File scelto per la categoria; se scelta=None usa il primo disponibile."""
    opts = _opzioni(nome_prefix)
    if scelta:
        for o in opts:
            if o.name == scelta:
                return o
    return opts[0] if opts else None


def _mix_sottofondo(voce, musica, dest):
    """Mixa una puntata (voce) con musica in loop a basso volume sotto. La musica si
    accorcia alla durata della voce (duration=first). Ritorna True se ok."""
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                        "-i", str(voce), "-stream_loop", "-1", "-i", str(musica),
                        "-filter_complex",
                        f"[1:a]volume={SOTTOFONDO_VOL}[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[out]",
                        "-map", "[out]", "-acodec", "libmp3lame", "-q:a", "3", str(dest)],
                       capture_output=True, text=True)
    return r.returncode == 0 and dest.exists()


def unisci_con_musica(files, dest, scelta=None):
    """files=[Path]. Costruisce il podcast completo con musica.
    scelta = {'intro':nomefile, 'stacco':nomefile, 'sottofondo':nomefile} (dai bottoni del bot),
    None per ognuna = usa la prima opzione disponibile in jingles/.
    - sottofondo -> ogni puntata mixata con musica sotto la voce
    - intro/stacco -> messi ai confini tra le puntate"""
    scelta = scelta or {}
    intro = _jingle("intro", scelta.get("intro"))
    stacco = _jingle("stacco", scelta.get("stacco"))
    sotto = _jingle("sottofondo", scelta.get("sottofondo"))
    tmpdir = dest.parent
    puntate = [f for f in files if f.exists() and f.stat().st_size > 1000]
    if not puntate:
        return False

    # 1. se c'è sottofondo, mixa ogni puntata (voce + musica sotto)
    lavorate = []
    for i, f in enumerate(puntate):
        if sotto:
            mixata = tmpdir / f"_mix_{i}_{f.name}"
            if _mix_sottofondo(f, sotto, mixata):
                lavorate.append(mixata)
            else:
                lavorate.append(f)  # se il mix fallisce, usa la voce nuda
        else:
            lavorate.append(f)

    # 2. sequenza finale con intro/stacco ai confini
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
    for m in lavorate:  # pulisci i mix temporanei
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
            "musica": {"intro": None, "stacco": None, "sottofondo": None}}

MODI = {"noi": "🎼 Solo noi (intro/finale/stacchi)",
        "ibrido": "🎛 Ibrido (noi + host segnalano)",
        "host": "🎙 Decidono gli host (marker nel parlato)"}


def kb_musica(setup):
    """Menu per SCEGLIERE tra le opzioni sonore disponibili in jingles/."""
    righe = []
    for cat, etichetta in (("intro", "🎬 Sigla"), ("stacco", "🔔 Stacco"), ("sottofondo", "🎵 Sottofondo")):
        opts = _opzioni(cat)
        scelto = setup.get("musica", {}).get(cat)
        if not opts:
            righe.append([B(f"{etichetta}: (nessun file — mettili in jingles/)", callback_data="noop")])
            continue
        # nome scelto (o "auto" = prima opzione)
        nome_scelto = scelto or (opts[0].name if opts else "—")
        righe.append([B(f"{etichetta}: {nome_scelto[:28]}", callback_data="noop")])
        # una riga di bottoni per le opzioni (max 3 per non intasare)
        riga = []
        for o in opts[:4]:
            mark = "🔘" if o.name == nome_scelto else "▫️"
            riga.append(B(f"{mark} {o.stem.replace(cat+'_','').replace(cat,'')[:14] or 'base'}",
                          callback_data=f"mus:{cat}:{o.name[:40]}"))
        righe.append(riga)
    righe.append([B("↩️ Indietro", callback_data="mus_back")])
    return KB(righe)


# ---------- menu principale ----------

def kb_menu():
    return KB([
        [B("🎬 Nuovo podcast", callback_data="m_nuovo")],
        [B("📼 I miei podcast", callback_data="m_vecchi"),
         B("📜 I miei prompt", callback_data="m_prompt")],
        [B("ℹ️ Stato", callback_data="m_stato"),
         B("❓ Aiuto", callback_data="m_help")],
    ])


async def menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_message("🎙️ PodcastLab — cosa facciamo?", reply_markup=kb_menu())


# ---------- pannello nuovo podcast ----------

def kb_pannello(s):
    n_musica = sum(1 for c in ("intro", "stacco", "sottofondo") if _opzioni(c))
    return KB([
        [B("➖", callback_data="n-"), B(f"🎙 {s['n']} puntate", callback_data="noop"), B("➕", callback_data="n+")],
        [B("🌐 Ricerca: DEEP (completa)" if s["deep"] else "⚡ Ricerca: VELOCE", callback_data="mode")],
        [B(f"✏️ Prompt: {s['extra_nome'] or 'standard'}", callback_data="p_menu")],
        [B(f"🎵 Musica ({n_musica} tipi)" if n_musica else "🎵 Musica (nessuna in jingles/)", callback_data="mus_menu")],
        [B("▶️ VAI!", callback_data="go"), B("🏠 Menu", callback_data="m_home")],
    ])


def txt_pannello(ud):
    s = ud["setup"]
    t = (10 if s["deep"] else 4) + s["n"] * 8
    topic = ud['topic'] if len(ud['topic']) <= 100 else ud['topic'][:100] + "…"  # no muro di testo
    return (f"🎬 {topic}\n\nRegola e premi ▶️ VAI!\n⏱ stimato: ~{t}-{t + 15} min")


def kb_prompt_menu():
    righe = [[B("📝 Crea nuovo prompt", callback_data="p_nuovo")],
             [B("🔙 Usa standard", callback_data="p_std")]]
    for i, c in enumerate(carica_custom()[:6]):
        righe.append([B(f"⭐ {c['nome'][:35]}", callback_data=f"p_use:{i}"),
                      B("🗑", callback_data=f"p_del:{i}")])
    righe.append([B("↩️ Indietro", callback_data="p_back")])
    return KB(righe)


# ---------- handlers ----------

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙️ PodcastLab!\nScrivi un argomento (es: storia di roma) oppure usa il menu 👇")
    await menu(update, ctx)


async def testo_libero(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    attesa = ctx.user_data.get("attesa")
    if attesa == "prompt_testo":
        ctx.user_data["nuovo_prompt"] = testo
        ctx.user_data["attesa"] = "prompt_nome"
        await update.message.reply_text("👍 Ora dagli un nome corto (es: 'stile ironico'):")
        return
    if attesa == "prompt_nome":
        lista = carica_custom()
        lista.insert(0, {"nome": testo[:50], "testo": ctx.user_data.pop("nuovo_prompt")})
        salva_custom(lista[:20])
        ctx.user_data["attesa"] = None
        s = ctx.user_data.setdefault("setup", setup_default())
        s["extra"] = " Inoltre: " + lista[0]["testo"]
        s["extra_nome"] = lista[0]["nome"]
        if ctx.user_data.get("topic"):
            await update.message.reply_text(txt_pannello(ctx.user_data), reply_markup=kb_pannello(s))
        else:
            await update.message.reply_text("⭐ Salvato e selezionato! Ora scrivi l'argomento del podcast.")
        return
    if attesa == "topic":
        ctx.user_data["attesa"] = None
    if len(testo) < 3:
        await update.message.reply_text("Argomento troppo corto 🙂")
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

    # --- menu principale (funziona SEMPRE, anche dopo riavvio bot) ---
    if d == "m_home":
        await q.edit_message_text("🎙️ PodcastLab — cosa facciamo?", reply_markup=kb_menu())
        return
    if d == "m_nuovo":
        ud["attesa"] = "topic"
        await q.edit_message_text("🎬 Scrivimi l'argomento del podcast (es: storia di roma) 👇")
        return
    if d == "m_vecchi":
        # mostra i podcast COMPLETI (_UNITO); se un merge è fallito, cadi sui singoli
        uniti = sorted(OUT.glob("*_UNITO.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]
        mp3s = uniti or sorted(OUT.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]
        if not mp3s:
            await q.edit_message_text("📼 Ancora nessun podcast!", reply_markup=kb_menu())
            return
        righe = [[B(f"🎧 {f.stem.replace('_UNITO','')[:45]}", callback_data=f"v_send:{f.name[:55]}")] for f in mp3s]
        righe.append([B("🏠 Menu", callback_data="m_home")])
        await q.edit_message_text("📼 Tocca per riascoltare:", reply_markup=KB(righe))
        return
    if d.startswith("v_send:"):
        nome = d[7:]
        matches = [f for f in OUT.glob("*.mp3") if f.name.startswith(nome[:50])]
        if matches and matches[0].stat().st_size >= 49 * 1024 * 1024:
            await chat.send_message(f"ℹ️ File troppo grande per Telegram (>50MB). È sul PC: {matches[0]}")
        elif matches:
            await chat.send_chat_action(ChatAction.UPLOAD_VOICE)
            await chat.send_audio(audio=open(matches[0], "rb"), title=matches[0].stem)
        else:
            await chat.send_message("⚠️ File non trovato sul PC.")
        return
    if d == "m_prompt" or d == "p_back":
        await q.edit_message_text("✏️ Prompt per gli host del podcast:", reply_markup=kb_prompt_menu())
        return
    if d == "m_stato":
        mp3s = sorted(OUT.glob("*.mp3"))
        lav = ud.get("lavoro_in_corso")
        testo = f"🗂 {len(mp3s)} mp3 sul PC.\n"
        testo += f"⏳ In corso: {lav}" if lav else "Nessun lavoro in corso."
        await q.edit_message_text(testo, reply_markup=kb_menu())
        return
    if d == "m_help":
        await q.edit_message_text(
            "❓ Come funziona:\n"
            "1. Scrivi un argomento qualsiasi in chat\n"
            "2. Regoli puntate/ricerca/prompt con i bottoni\n"
            "3. ▶️ VAI! e aspetti: arrivano gli mp3 qui\n\n"
            "📜 I prompt personalizzati si salvano e riusano.\n"
            "📼 I podcast vecchi si riascoltano dal menu.", reply_markup=kb_menu())
        return

    # --- menu musica: scegli tra le opzioni sonore ---
    if d == "mus_menu":
        await q.edit_message_text(
            "🎵 Scegli le musiche (metti più file in jingles/ per avere opzioni):",
            reply_markup=kb_musica(s))
        return
    if d.startswith("mus:"):  # mus:categoria:nomefile
        _, cat, nome = d.split(":", 2)
        s.setdefault("musica", {})[cat] = nome
        await q.edit_message_text("🎵 Scegli le musiche:", reply_markup=kb_musica(s))
        return
    if d == "mus_back":
        await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s))
        return

    # --- menu prompt ---
    if d == "p_menu":
        await q.edit_message_text("✏️ Prompt per gli host:", reply_markup=kb_prompt_menu())
        return
    if d == "p_std":
        s["extra"], s["extra_nome"] = "", ""
    elif d == "p_nuovo":
        ud["attesa"] = "prompt_testo"
        await q.edit_message_text(
            "📝 Scrivimi le istruzioni extra per gli host, italiano libero.\n\n"
            "Esempi:\n• «tono ironico, esempi pratici, spiega semplice»\n"
            "• «stile prof universitario, cita le fonti»\n"
            "• «ritmo veloce, domande retoriche»\n\nScrivi e invia 👇")
        return
    elif d.startswith("p_use:"):
        try:
            c = carica_custom()[int(d.split(":")[1])]
            s["extra"], s["extra_nome"] = " Inoltre: " + c["testo"], c["nome"]
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
        await q.edit_message_text("🗑 Cancellato.", reply_markup=kb_prompt_menu())
        return

    # --- pannello nuovo podcast ---
    if d in ("p_std",) or d.startswith("p_use:"):
        if ud.get("topic"):
            await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s))
        else:
            await q.edit_message_text("⭐ Selezionato! Scrivi l'argomento del podcast 👇")
        return
    if not ud.get("topic"):
        await q.edit_message_text("🎙️ PodcastLab — cosa facciamo?", reply_markup=kb_menu())
        return
    if d == "noop":
        return
    if d == "n+":
        s["n"] = min(8, s["n"] + 1)
    elif d == "n-":
        s["n"] = max(1, s["n"] - 1)
    elif d == "mode":
        s["deep"] = not s["deep"]
    elif d == "go":
        if ud.get("lavoro_in_corso"):  # blocca doppio-avvio (spam VAI / secondo argomento)
            await q.answer("⚠️ Un podcast è già in elaborazione!", show_alert=True)
            return
        await q.edit_message_text(f"🚀 Si parte: {ud['topic']}")
        await esegui(chat, ctx)
        return
    await q.edit_message_text(txt_pannello(ud), reply_markup=kb_pannello(s))


def slug(testo):
    """Nome file sicuro su Windows/Drive: niente \\/:*?\"<>| e spazi->_."""
    return re.sub(r'[\\/*?:"<>|]', '', testo[:40]).replace(' ', '_').strip('_') or "podcast"


async def esegui(chat, ctx):
    ud = ctx.user_data
    topic, s = ud["topic"], ud["setup"]
    n, deep, extra = s["n"], s["deep"], s["extra"]
    marker = MARKER_ISTR if s.get("modo") in ("ibrido", "host") else ""  # host segnalano solo in ibrido/host
    ud["lavoro_in_corso"] = topic
    base = slug(topic)
    msg = await chat.send_message(
        f"🔬 {topic} — {n} puntate ({'deep' if deep else 'veloce'})\n\n"
        f"{bar(0.05)} Fase 1/3: cerco fonti sul web…\n(ti scrivo io: puoi chiudere Telegram)")
    loop = asyncio.get_running_loop()

    def avvisa(frac, testo):
        asyncio.run_coroutine_threadsafe(
            msg.edit_text(f"🔬 {topic} — {n} puntate\n\n{bar(frac)} {testo}"), loop)
        asyncio.run_coroutine_threadsafe(chat.send_chat_action(ChatAction.RECORD_VOICE), loop)

    def lavoro():
        nb = cli(["create", topic[:80]])
        nb_id = nb.get("id") or nb.get("notebook", {}).get("id")
        if not nb_id:
            return f"Non riesco a creare il notebook 😞 Riprova tra poco.\n(dettaglio: {nb})"
        r = cli(["source", "add-research", "-n", nb_id, topic, "--mode", "deep" if deep else "fast"],
                timeout=3600)
        if r.get("error"):
            return f"La ricerca web non è partita 😞\n(dettaglio: {r})"
        avvisa(0.15, "Fase 1/3: leggo e scelgo le fonti…")
        w = cli(["research", "wait", "-n", nb_id, "--import-all", "--timeout", "1800"], timeout=2000)
        if w.get("error"):
            return f"Ricerca web fallita o troppo lenta 😞\n(dettaglio: {w})"
        avvisa(0.25, f"Fonti OK! 🧩 Divido in {n} macro-temi…")
        temi = macro_temi(nb_id, topic, n)
        files = []
        for i, tema in enumerate(temi, 1):
            avvisa(0.25 + 0.65 * (i - 1) / n, f"Fase 2/3: 🎙 puntata {i}/{n}\n{tema}")
            prompt = PART_PROMPT.format(i=i, n=n, tema=tema, marker=marker, extra=extra)
            g = cli(["generate", "audio", prompt, "-n", nb_id,
                     "--length", "long", "--wait", "--timeout", "1800"], timeout=2000)
            # generate ritorna {task_id, status, url}, NON artifact_id -> lo prendo da artifact list
            art_id = g.get("artifact_id") or g.get("id")
            if not art_id and g.get("status") == "completed":
                audio = [a for a in cli(["artifact", "list", "-n", nb_id]).get("artifacts", [])
                         if a.get("type_id") == "audio" and a.get("status_id") == 3]
                audio.sort(key=lambda a: a.get("created_at", ""), reverse=True)
                art_id = audio[0]["id"] if audio else None
            if not art_id:
                return f"La puntata {i} ({tema}) non è venuta 😞\n(dettaglio: {g})"
            mp3 = OUT / f"{base}_parte{i}.mp3"
            cli(["download", "audio", "-n", nb_id, "-a", art_id, str(mp3)])
            (PROMPTS_DIR / f"{mp3.stem}.json").write_text(json.dumps(
                {"topic": topic, "parte": i, "tema": tema, "prompt": prompt,
                 "notebook_id": nb_id, "artifact_id": art_id}, ensure_ascii=False, indent=1),
                encoding="utf-8")
            files.append((mp3, tema))
            cli(["artifact", "delete", art_id, "-n", nb_id])  # 1 audio/notebook -> libera slot
        avvisa(0.95, "Fase 3/3: 🎵 unisco puntate + sigla e stacchi…")
        unito = OUT / f"{base}_UNITO.mp3"
        ok = unisci_con_musica([f for f, _ in files], unito, s.get("musica"))
        return {"files": files, "unito": unito if ok else None, "temi": temi}

    try:
        result = await asyncio.to_thread(lavoro)
    except Exception as e:
        ud["lavoro_in_corso"] = None  # blinda il lock: se lavoro() crasha, non resta appeso
        await msg.edit_text(f"❌ Errore imprevisto: {str(e)[:200]}")
        await chat.send_message("🏠 Menu:", reply_markup=kb_menu())
        return
    ud["lavoro_in_corso"] = None
    if isinstance(result, str):
        await msg.edit_text(f"❌ {result}")
        await chat.send_message("🏠 Menu:", reply_markup=kb_menu())
        return
    temi_txt = "\n".join(f"  {i}. {t}" for i, t in enumerate(result["temi"], 1))
    await msg.edit_text(f"🎉 {topic} pronto!\n\n{bar(1)} 100%\n\n📚 Puntate:\n{temi_txt}")
    for i, (f, tema) in enumerate(result["files"], 1):
        if f.exists() and f.stat().st_size > 1000:
            await chat.send_chat_action(ChatAction.UPLOAD_VOICE)
            await chat.send_audio(audio=open(f, "rb"), title=f"Parte {i}: {tema[:50]}",
                                  caption=f"🎙 Parte {i}/{len(result['files'])} — {tema}")
    u = result["unito"]
    if u and u.exists() and u.stat().st_size < 49 * 1024 * 1024:
        await chat.send_chat_action(ChatAction.UPLOAD_VOICE)
        await chat.send_audio(audio=open(u, "rb"), title=f"{topic} — COMPLETO",
                              caption="🎧 Tutte le puntate in un file solo")
    elif u:
        await chat.send_message(f"ℹ️ Il file unito supera 50MB: è sul PC in {u}")
    await chat.send_message("🎧 Buon ascolto!", reply_markup=kb_menu())


async def test_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Test bottone:", reply_markup=KB([[B("👍 Funziona!", callback_data="noop")]]))


async def on_error(update, ctx):
    log.error("Errore handler: %s", ctx.error, exc_info=ctx.error)
    try:
        if update and update.effective_chat:
            await update.effective_chat.send_message(
                f"⚠️ Ops: {str(ctx.error)[:200]}", reply_markup=kb_menu())
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
    log.info("PodcastLab bot avviato (v4 menu)")
    app.run_polling()


if __name__ == "__main__":
    main()
