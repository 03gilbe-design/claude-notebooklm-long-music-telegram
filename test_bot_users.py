"""Fa girare gli handler VERI di bot.py con utenti Telegram FINTI (niente account/rete).

Simula update reali (comandi, testo, click bottoni) e li passa agli handler del bot.
Mocka solo i confini esterni: cli() (notebooklm) e le API Telegram (send/edit/answer).
Cattura errori runtime che il solo leggere il codice non trova: KeyError su user_data,
callback rotti, crash negli handler, lock non liberato, ecc.

Uso: python test_bot_users.py
"""
import asyncio
import sys
import types
from unittest import mock

try:
    sys.stdout.reconfigure(encoding="utf-8")  # emoji/accenti anche su terminale Windows cp1252
except Exception:
    pass

# --- stub del modulo telegram PRIMA di importare bot (così import non fallisce) ---
def _kb(rows): return {"kind": "keyboard", "rows": rows}
def _btn(text, callback_data=None): return {"text": text, "cb": callback_data}

telegram = types.ModuleType("telegram")
telegram.InlineKeyboardButton = _btn
telegram.InlineKeyboardMarkup = _kb
telegram.Update = object
constants = types.ModuleType("telegram.constants")
constants.ChatAction = types.SimpleNamespace(TYPING="typing", RECORD_VOICE="rec", UPLOAD_VOICE="up")
telegram.constants = constants
ext = types.ModuleType("telegram.ext")
for n in ("Application","CallbackQueryHandler","CommandHandler","ContextTypes","MessageHandler","filters"):
    setattr(ext, n, mock.MagicMock())
ext.ContextTypes = types.SimpleNamespace(DEFAULT_TYPE=object)
telegram.ext = ext
sys.modules["telegram"] = telegram
sys.modules["telegram.constants"] = constants
sys.modules["telegram.ext"] = ext

# .env fittizio (bot.py lo legge all'import)
import os, tempfile, pathlib
TMP = pathlib.Path(tempfile.mkdtemp())
(TMP/".env").write_text("TELEGRAM_TOKEN=fake:token\nN_PARTI=3\n")
os.chdir(TMP)
# bot.py sta in C:\podcastlab -> import da lì ma con cwd=TMP per .env e out/
sys.path.insert(0, r"C:\podcastlab")
# copia .env dove bot lo cerca (BASE = cartella di bot.py)
(pathlib.Path(r"C:\podcastlab")/".env").exists() or (pathlib.Path(r"C:\podcastlab")/".env").write_text("TELEGRAM_TOKEN=fake:token\nN_PARTI=3\n")

import bot

# NEVER write test mp3s into the real out/ folder — isolate to a temp dir
import tempfile
bot.OUT = pathlib.Path(tempfile.mkdtemp(prefix="podcastlab_test_out_"))
bot.PROMPTS_DIR = bot.OUT / "prompts"
bot.PROMPTS_DIR.mkdir(exist_ok=True)

# --- finti oggetti Telegram che REGISTRANO cosa fa il bot ---
class FakeMsg:
    def __init__(self, log): self.log = log; self.message_id = 1; self.text = ""
    async def edit_text(self, t, **k): self.text = t; self.log.append(("edit", t[:60]))
    async def reply_text(self, t, **k): self.log.append(("reply", t[:60])); return FakeMsg(self.log)
    async def reply_audio(self, **k): self.log.append(("audio", k.get("title","")))
    async def reply_chat_action(self, a): pass

class FakeChat:
    def __init__(self, log): self.log = log
    async def send_message(self, t, **k): self.log.append(("send", t[:60])); return FakeMsg(self.log)
    async def send_audio(self, **k): self.log.append(("audio", k.get("title","")))
    async def send_chat_action(self, a): pass

class FakeQuery:
    def __init__(self, data, chat, log): self.data=data; self._chat=chat; self.log=log; self.message=FakeMsg(log)
    async def answer(self): pass
    async def edit_message_text(self, t, **k): self.log.append(("qedit", t[:60]))

class FakeUpdate:
    def __init__(self, log, text=None, data=None, chat=None):
        self.log = log; self._chat = chat or FakeChat(log)
        self.message = FakeMsg(log); self.message.text = text or ""
        self.effective_chat = self._chat
        self.callback_query = FakeQuery(data, self._chat, log) if data else None

def ctx_new():
    c = types.SimpleNamespace(); c.user_data = {}; c.args = []; return c


async def scenario(nome, passi, ctx):
    """passi: lista di ('msg', testo) / ('cmd', args) / ('click', callback_data)."""
    log = []
    print(f"\n=== {nome} ===")
    for kind, val in passi:
        try:
            if kind == "msg":
                await bot.testo_libero(FakeUpdate(log, text=val), ctx)
            elif kind == "cmd_start":
                await bot.start(FakeUpdate(log, text=val), ctx)
            elif kind == "click":
                await bot.bottoni(FakeUpdate(log, data=val), ctx)
        except Exception as e:
            import traceback
            print(f"  ❌ CRASH su {kind}:{val!r} -> {type(e).__name__}: {e}")
            traceback.print_exc()
            return False
    for a, t in log[-6:]:
        print(f"  [{a}] {t}")
    return True


async def main():
    # NEVER touch the real prompt_personalizzati.json — tests use an in-memory fake
    _fake_prompts = []
    bot.carica_custom = lambda: list(_fake_prompts)
    def _salva(lista):
        _fake_prompts.clear(); _fake_prompts.extend(lista)
    bot.salva_custom = _salva
    # mocka cli() = notebooklm: finge tutto ok, veloce
    def fake_cli(args, timeout=1800):
        a0 = args[0]
        if a0 == "create": return {"id": "nb_test"}
        if a0 == "ask": return {"answer": "Tema uno\nTema due\nTema tre"}
        if a0 == "generate": return {"artifact_id": "art1"}
        if a0 == "download":  # crea un mp3 finto VERO (>1000 byte) al path richiesto
            open(args[-1], "wb").write(b"x" * 2000); return {"ok": True}
        return {"ok": True}
    bot.cli = fake_cli
    def fake_unisci(files, dest):  # crea davvero il file unito
        open(dest, "wb").write(b"x" * 3000); return True
    bot.unisci_con_musica = fake_unisci
    # download finto: crea un mp3 vuoto così i controlli file passano
    orig_esegui_download = None

    ok = True
    # 1. utente base: /start poi menu
    ok &= await scenario("Utente base — /start", [("cmd_start", "/start")], ctx_new())
    # 2. user sends topic -> panel
    c = ctx_new()
    ok &= await scenario("User sends topic", [("msg", "storia di roma")], c)
    # 3. click buttons: +episodes, cambia ricerca, prompt menu
    ok &= await scenario("Regola pannello", [("click","n+"),("click","mode"),("click","p_menu"),("click","p_std")], c)
    # 4. LETHAL title (Windows-illegal chars)
    ok &= await scenario("Title with /:? ", [("msg", "USA/URSS: guerra? 🚀")], ctx_new())
    # 5. click su bottone di sessione MORTA (user_data vuoto)
    ok &= await scenario("Bottone sessione scaduta", [("click","n+")], ctx_new())
    # 6. menu: vecchi podcast, prompt, stato, help, home
    for d in ("m_vecchi","m_prompt","m_stato","m_help","m_home","m_nuovo"):
        ok &= await scenario(f"Menu -> {d}", [("click", d)], ctx_new())
    # 7. crea prompt nuovo (flusso testo->nome)
    c = ctx_new()
    ok &= await scenario("Crea prompt custom", [
        ("msg","storia di roma"),("click","p_menu"),("click","p_nuovo"),
        ("msg","tono ironico"),("msg","stile ironico")], c)
    # 8. flusso COMPLETO fino a VAI (esegui con cli mockato)
    c = ctx_new()
    ok &= await scenario("Flusso completo -> VAI", [("msg","test topic"),("click","go")], c)

    # ===== SCENARI AVVERSARIALI (cerco io i prossimi bug) =====
    # 9. cli create fallisce -> il bot deve dare errore pulito, non crashare
    bot.cli = lambda args, timeout=1800: {"error": True, "message": "boom"} if args[0]=="create" else {"ok":True}
    c = ctx_new()
    ok &= await scenario("cli create FALLISCE", [("msg","x fallito"),("click","go")], c)

    # 10. ask (macro_temi) ritorna vuoto -> deve usare fallback temi generici
    def cli_ask_vuoto(args, timeout=1800):
        if args[0]=="create": return {"id":"nb"}
        if args[0]=="ask": return {"answer": ""}
        if args[0]=="generate": return {"artifact_id":"a"}
        if args[0]=="download": open(args[-1],"wb").write(b"x"*2000); return {"ok":True}
        return {"ok":True}
    bot.cli = cli_ask_vuoto
    c = ctx_new()
    ok &= await scenario("ask vuoto (fallback temi)", [("msg","tema senza risposta"),("click","go")], c)

    # 11. generate fallisce alla parte 2 -> errore pulito, lock liberato
    stato = {"n":0}
    def cli_gen_fail(args, timeout=1800):
        if args[0]=="create": return {"id":"nb"}
        if args[0]=="ask": return {"answer":"a\nb\nc"}
        if args[0]=="generate":
            stato["n"]+=1
            return {"artifact_id":"a"} if stato["n"]==1 else {"error":True}
        if args[0]=="download": open(args[-1],"wb").write(b"x"*2000); return {"ok":True}
        return {"ok":True}
    bot.cli = cli_gen_fail
    c = ctx_new()
    ok &= await scenario("generate fallisce a metà", [("msg","meta fail"),("click","go")], c)
    print("   lock dopo fail:", c.user_data.get("lavoro_in_corso"), "(deve essere None)")

    # 12. click prompt_use su indice inesistente (nessun prompt salvato)
    c = ctx_new(); c.user_data["topic"]="x"; c.user_data["setup"]=bot.setup_default()
    ok &= await scenario("prompt_use indice fuori range", [("click","p_use:99")], c)
    # 13. p_del fuori range
    ok &= await scenario("p_del fuori range", [("click","p_del:99")], c)
    # 14. messaggio troppo corto
    ok &= await scenario("messaggio 1 char", [("msg","x")], ctx_new())
    # 15. v_send su file inesistente
    ok &= await scenario("v_send file mancante", [("click","v_send:non_esiste.mp3")], ctx_new())
    # 16. doppio go di fila (race lock)
    c = ctx_new(); bot.cli = fake_cli; bot.unisci_con_musica = fake_unisci
    ok &= await scenario("doppio go", [("msg","doppio"),("click","go"),("click","go")], c)
    # 17. callback ignoto (bottone di versione vecchia)
    ok &= await scenario("callback sconosciuto", [("click","xyz_vecchio")], ctx_new())
    # 18. topic only emoji
    ok &= await scenario("topic only emoji", [("msg","🚀🎙️🔥")], ctx_new())
    # 19. topic only numbers
    ok &= await scenario("numeric topic", [("msg","12345")], ctx_new())
    # 20. prompt custom VUOTO (invio spazio come istruzione)
    c = ctx_new()
    ok &= await scenario("prompt custom vuoto", [
        ("msg","tema x"),("click","p_menu"),("click","p_nuovo"),("msg","   "),("msg","nome")], c)
    # 21. nome prompt vuoto
    c = ctx_new()
    ok &= await scenario("nome prompt vuoto", [
        ("msg","tema y"),("click","p_menu"),("click","p_nuovo"),("msg","istruzione"),("msg","")], c)

    print("\n" + ("✅ TUTTI gli scenari senza crash" if ok else "❌ Trovati crash sopra"))
    return ok

if __name__ == "__main__":
    sys.exit(0 if asyncio.run(main()) else 1)
