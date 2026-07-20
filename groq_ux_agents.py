"""Groq LLM agents act as FAKE USERS on the real bot handlers (all mocked, zero NotebookLM).

Each persona has a goal, sees the real bot messages+buttons, picks the next action,
and reports: questions, doubts, improvement ideas. Everything saved to UX_REPORT.md.

Usage: python groq_ux_agents.py
"""
import asyncio
import json
import os
import re
import sys
import urllib.request

# reuse the whole fake-telegram harness (stubs telegram, imports bot) — no scenarios run on import
import test_bot_users as h
bot = h.bot

GROQ_KEY = None
for envp in (r"C:\Users\Gilberto Bizzo\.env", os.path.join(os.path.dirname(__file__), ".env")):
    if os.path.exists(envp):
        for line in open(envp, encoding="utf-8"):
            if line.startswith("GROQ_API_KEY="):
                GROQ_KEY = line.split("=", 1)[1].strip()
MODEL = "llama-3.3-70b-versatile"


def groq(messages, retries=2):
    body = json.dumps({"model": MODEL, "messages": messages, "temperature": 0.7,
                       "response_format": {"type": "json_object"}}).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json",
                "User-Agent": "curl/8.0"})
    for _ in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(json.loads(r.read())["choices"][0]["message"]["content"])
        except Exception as e:
            err = e
    return {"error": str(err)}


# ---- fake bot environment (NEVER touches NotebookLM) ------------------------
def fake_cli(args, timeout=1800):
    a0 = args[0]
    if a0 == "list":
        return {"notebooks": [
            {"id": "nb1", "title": "Storia di Roma antica"},
            {"id": "nb2", "title": "Intelligenza Artificiale Generativa"}]}
    if a0 == "source" and args[1] == "list":
        return {"sources": [{"title": "Wikipedia - Roma"}, {"title": "Treccani - Impero"},
                            {"title": "PDF lezioni universitarie"}]}
    if a0 == "create": return {"id": "nb_fake"}
    if a0 == "ask": return {"answer": "Tema uno\nTema due\nTema tre"}
    if a0 == "generate": return {"artifact_id": "art1"}
    if a0 == "download":
        open(args[-1], "wb").write(b"x" * 2000); return {"ok": True}
    return {"ok": True}


class Capture:
    """Collects what the bot shows: last message text + keyboard buttons."""
    def __init__(self):
        self.text = ""
        self.buttons = []  # [(label, callback_data)]

    def record(self, t, kb=None):
        self.text = t
        self.buttons = []
        if isinstance(kb, dict) and kb.get("kind") == "keyboard":
            for row in kb["rows"]:
                for b in row:
                    self.buttons.append((b["text"], b.get("cb")))


async def drive(persona, goal, max_steps=10):
    cap = Capture()
    log = []

    class Msg(h.FakeMsg):
        async def edit_text(self, t, **k): cap.record(t, k.get("reply_markup"))
        async def reply_text(self, t, **k): cap.record(t, k.get("reply_markup")); return Msg(log)

    class Query(h.FakeQuery):
        async def edit_message_text(self, t, **k): cap.record(t, k.get("reply_markup"))

    class Upd(h.FakeUpdate):
        def __init__(self, text=None, data=None):
            super().__init__(log, text=text, data=data)
            if text is not None:
                self.message = Msg(log); self.message.text = text
            if data is not None:
                self.callback_query = Query(data, None, log)

    ctx = h.ctx_new()
    feedback = []
    await bot.start(Upd(text="/start"), ctx)
    for step in range(max_steps):
        btns = "\n".join(f"- [{lbl}] -> {cb}" for lbl, cb in cap.buttons) or "(no buttons: bot expects FREE TEXT)"
        ans = groq([
            {"role": "system", "content":
             f"You are '{persona}', testing an Italian Telegram bot that creates podcasts. Your goal: {goal}. "
             "You see the bot's last message and its buttons. Reply ONLY JSON: "
             '{"action":"click"|"type"|"done", "value":"<callback_data or text>", '
             '"questions":[], "doubts":[], "improvements":[]} '
             "Report REAL UX issues you notice as a user: unclear labels, missing back buttons, "
             "missing previews, confusing flow, formatting (bold/lists) that would help. Be concrete and brief."},
            {"role": "user", "content": f"BOT MESSAGE:\n{cap.text}\n\nBUTTONS:\n{btns}\n\nStep {step+1}/{max_steps}."}])
        if ans.get("error"):
            feedback.append({"step": step, "error": ans["error"]}); break
        for k in ("questions", "doubts", "improvements"):
            for item in ans.get(k) or []:
                feedback.append({"persona": persona, "step": step, "type": k,
                                 "text": item, "screen": cap.text[:80]})
        act, val = ans.get("action"), str(ans.get("value") or "")
        if act == "done" or not act:
            break
        try:
            if act == "click" and val:
                await bot.bottoni(Upd(data=val), ctx)
            elif act == "type" and val:
                await bot.testo_libero(Upd(text=val), ctx)
        except Exception as e:
            feedback.append({"persona": persona, "step": step, "type": "CRASH",
                             "text": f"{act}:{val} -> {type(e).__name__}: {e}", "screen": cap.text[:80]})
            break
    return feedback


async def main():
    bot.cli = fake_cli
    bot.unisci_con_musica = lambda files, dest, scelta=None: (open(dest, "wb").write(b"x" * 3000), True)[1]

    personas = [
        ("Nonna Pina, 70 anni, poco tecnologica", "capire come creare un podcast sulla cucina"),
        ("Marco, studente frettoloso", "rigenerare episodi da un notebook esistente SENZA rifare la ricerca"),
        ("Giulia, precisa e diffidente", "vedere ESATTAMENTE cosa contiene un prompt e un notebook prima di usarli"),
        ("Luca, power user", "creare un prompt personalizzato, salvarlo e riusarlo"),
        ("Sara, curiosa", "riascoltare un vecchio podcast e capire lo stato del lavoro"),
    ]
    all_fb = []
    for p, g in personas:
        print(f"agent: {p[:30]}...", flush=True)
        all_fb += await drive(p, g)

    out = ["# UX Report — Groq fake-user agents\n"]
    for tipo in ("CRASH", "doubts", "questions", "improvements"):
        items = [f for f in all_fb if f.get("type") == tipo]
        if items:
            out.append(f"\n## {tipo} ({len(items)})\n")
            for f in items:
                out.append(f"- **{f['persona'].split(',')[0]}** (step {f['step']}, su «{f['screen'][:50]}»): {f['text']}")
    report = "\n".join(out)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "UX_REPORT.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nsaved {out_path} — {len(all_fb)} feedback items")

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    asyncio.run(main())
