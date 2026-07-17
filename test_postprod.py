import json
import subprocess
from pathlib import Path
import os

def create_fake_mp3(filename, duration=3):
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(duration), filename], check=True)

print("Creating fake files...")
create_fake_mp3("test1.mp3")
create_fake_mp3("test2.mp3")

json_data1 = {
    "segments": [
        {
            "words": [
                {"word": "ciao", "start": 0.0, "end": 0.5},
                {"word": "stacco", "start": 0.5, "end": 1.0},
                {"word": "musicale", "start": 1.0, "end": 1.5},
                {"word": "ok", "start": 1.5, "end": 2.0}
            ]
        }
    ]
}
Path("test1.json").write_text(json.dumps(json_data1))

json_data2 = {
    "segments": [
        {
            "words": [
                {"word": "fine", "start": 0.0, "end": 1.0}
            ]
        }
    ]
}
Path("test2.json").write_text(json.dumps(json_data2))

Path("jingles").mkdir(exist_ok=True)
create_fake_mp3("jingles/intro.mp3", 2)
create_fake_mp3("jingles/stacco.mp3", 1)

print("Running postprod.py...")
res = subprocess.run(["python", "postprod.py", "test1.mp3", "test1.json", "test2.mp3", "test2.json", "-o", "out_test.mp3"], capture_output=True, text=True)

print("Return code:", res.returncode)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)

if Path("out_test.mp3").exists():
    print("out_test.mp3 was created successfully.")
else:
    print("out_test.mp3 was NOT created.")
