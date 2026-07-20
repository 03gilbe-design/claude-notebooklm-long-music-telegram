import time

def out(s, d=0.4):
    print(s, flush=True)
    time.sleep(d)

out("Initializing Dataset Builder...", 0.6)
out("Loading 145 prompts and 61 audio files...", 1.2)
out("Processing segment 1/61... [OK]", 0.1)
out("Processing segment 2/61... [OK]", 0.1)
out("... fast forwarding ...", 0.5)
out("Processing segment 61/61... [OK]", 0.3)
out("Extracting text and audio pairs...", 0.8)
out("Aligning audio waveforms...", 0.6)
out("\033[92mDataset compilation complete!\033[0m", 0.2)
out("Saved to: ./dataset/podcast_dataset_v1.jsonl", 0.1)
