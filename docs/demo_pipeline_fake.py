"""Scripted fake output for the VHS demo recording — mirrors the real pipeline.py logs
so the GIF shows realistic behavior without needing NotebookLM auth / GPU during recording.
"""
import time
import sys

def out(s, d=0.4):
    print(s, flush=True)
    time.sleep(d)

out("==================================================")
out("1/2 Download audios from NotebookLM")
out("==================================================")
out("89 notebooks found")
out("Downloading: How data travels the network", 0.3)
out("Downloading: The origins of Rome", 0.3)
out("Downloading: AlphaEvolve and code selection", 0.3)
out("... 61 audios downloaded (resumed, skipped 0)", 0.6)
out("")
out("==================================================")
out("2/2 Recover prompts")
out("==================================================")
out("Recovered 145 real prompts + source links", 0.6)
out("")
out("==================================================")
out("STATUS PodcastLab")
out("==================================================")
out("audios downloaded:  61")
out("prompts recovered:  145")
out("", 0.3)
out("Next: run PodcastLab_Colab.ipynb on Colab GPU", 0.4)
out("  -> transcribe + diarize (2 speakers) + build dataset", 1.2)
