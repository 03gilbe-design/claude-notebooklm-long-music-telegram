import time

def out(s, d=0.4): print(s, flush=True); time.sleep(d)

out("Starting Telegram Bot...", 0.6)
out("Connecting to Telegram API... [\033[92mConnected\033[0m]", 0.4)
out("Bot is now polling for new messages.\n", 0.2)
out("\033[96m[User: @gilbe]\033[0m /generate_music", 1.5)
out("\033[93m[Bot]\033[0m Acknowledged. Context loaded.", 0.5)
out("\033[93m[Bot]\033[0m Calling Claude API for prompt formulation...", 1.2)
out("\033[93m[Bot]\033[0m Generating music stream via NotebookLM engine...", 2.0)
out("\033[93m[Bot]\033[0m Sending audio file back to user... [\033[92mSent\033[0m]", 0.5)
