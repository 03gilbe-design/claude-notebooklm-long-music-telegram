import os
import imageio.v3 as iio
from html2image import Html2Image

hti = Html2Image(size=(420, 950))
hti.output_path = "C:/podcastlab/docs/hq_temp"
os.makedirs(hti.output_path, exist_ok=True)

html_template = """
<!DOCTYPE html>
<html>
<head>
<style>
  body {
    margin: 0; padding: 0; background-color: #0e1621;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #fff; width: 420px; height: 950px; display: flex; flex-direction: column;
  }
  .header {
    background-color: #17212b; padding: 12px 18px; font-weight: bold; font-size: 16px;
    display: flex; align-items: center; border-bottom: 1px solid #000; box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    z-index: 10;
  }
  .chat-container {
    flex: 1; padding: 15px; display: flex; flex-direction: column; gap: 12px;
    background-image: radial-gradient(circle at top right, #111a25, #0e1621);
  }
  .msg-row { display: flex; width: 100%; }
  .msg-row.in { justify-content: flex-start; }
  .msg-row.out { justify-content: flex-end; }
  .msg {
    max-width: 82%; padding: 10px 14px; border-radius: 14px; font-size: 15px;
    line-height: 1.45; position: relative; box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }
  .msg.in { background-color: #182533; border-bottom-left-radius: 4px; }
  .msg.out { background-color: #2b5278; border-bottom-right-radius: 4px; }
  .msg-time { font-size: 11px; color: rgba(255,255,255,0.5); float: right; margin-top: 6px; margin-left: 10px; }
  
  .inline-keyboard { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; width: 100%; }
  .inline-btn {
    background-color: #202b36; color: #3390ec; text-align: center; padding: 12px;
    border-radius: 8px; font-size: 14px; font-weight: bold; cursor: pointer; transition: 0.2s;
  }
  
  .input-area {
    background-color: #17212b; padding: 12px 15px; color: #7f8991; font-size: 15px;
    display: flex; align-items: center; box-shadow: 0 -1px 3px rgba(0,0,0,0.2);
  }
  .input-area span { background-color: #242f3d; border-radius: 20px; padding: 12px 15px; flex: 1; }
  
  .status-box {
    background-color: #0e1621; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 10px; margin-top: 8px;
  }
  .status-header { display: flex; align-items: center; margin-bottom: 8px; font-weight: 600; font-size: 14px; }
  .status-icon { width: 24px; height: 24px; border-radius: 4px; margin-right: 10px; }
  .progress-bar-bg { background-color: #17212b; border-radius: 4px; height: 6px; width: 100%; overflow: hidden; margin-top: 6px; }
  .progress-bar-fill { height: 100%; transition: width 0.3s; }
  
  .audio-player {
    display: flex; align-items: center; background-color: #242f3d; padding: 12px; border-radius: 10px; margin-top: 10px;
  }
  .play-btn { width: 40px; height: 40px; background-color: #3390ec; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 12px; box-shadow: 0 2px 5px rgba(51,144,236,0.4); }
</style>
</head>
<body>
  <div class="header">
    <div style="width: 38px; height: 38px; background: linear-gradient(135deg, #4285F4, #8B5CF6); border-radius: 50%; margin-right: 12px; display:flex; align-items:center; justify-content:center; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
      <span style="font-size: 18px;">🎶</span>
    </div>
    <div style="line-height: 1.2;">Audio Architect Bot<br><span style="font-size: 12.5px; color: #3390ec; font-weight: normal;">bot</span></div>
  </div>
  <div class="chat-container">
    {content}
  </div>
  <div class="input-area"><span>Message...</span></div>
</body>
</html>
"""

# FASE 1: L'utente invia il comando
frame1 = """
<div class="msg-row out">
  <div class="msg out">
    /generate_music
    <span class="msg-time">14:00</span>
  </div>
</div>
"""

# FASE 2: Il Bot chiede lo stile musicale
frame2 = frame1 + """
<div class="msg-row in">
  <div style="max-width: 85%; width: 100%;">
    <div class="msg in" style="max-width: 100%; box-sizing: border-box;">
      Benvenuto! Quale genere vuoi orchestrare oggi partendo dalla documentazione AI? 🎵
      <span class="msg-time">14:00</span>
    </div>
    <div class="inline-keyboard">
      <div class="inline-btn">🎹 Ambient Cyberpunk</div>
      <div class="inline-btn">🎸 Rock Lo-Fi</div>
      <div class="inline-btn">🎧 Synthwave Orchestrale</div>
    </div>
  </div>
</div>
"""

# FASE 3: L'utente clicca un bottone
frame3 = frame2 + """
<div class="msg-row out">
  <div class="msg out">
    🎹 Ambient Cyberpunk
    <span class="msg-time">14:01</span>
  </div>
</div>
"""

# FASE 4: Ingestion in NotebookLM (Inizio)
frame4 = frame3 + """
<div class="msg-row in">
  <div class="msg in" style="width: 100%;">
    <div class="status-box">
      <div class="status-header">
        <img src="https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/google-docs.png" class="status-icon">
        <span style="color: #4285F4;">NotebookLM</span>
      </div>
      <span style="font-size: 13px; color: #7f8991;">Analisi documentazione in corso... (20%)</span>
      <div class="progress-bar-bg"><div class="progress-bar-fill" style="background-color: #4285F4; width: 20%;"></div></div>
    </div>
    <span class="msg-time">14:01</span>
  </div>
</div>
"""

# FASE 5: Ingestion in NotebookLM (Fine)
frame5 = frame3 + """
<div class="msg-row in">
  <div class="msg in" style="width: 100%;">
    <div class="status-box" style="border-color: rgba(66, 133, 244, 0.3); box-shadow: 0 0 10px rgba(66, 133, 244, 0.1);">
      <div class="status-header">
        <img src="https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/google-docs.png" class="status-icon">
        <span style="color: #4285F4;">NotebookLM</span>
      </div>
      <span style="font-size: 13px; color: #a4b3bf;">Analisi completata! (100%)<br><i style="font-size:11px;">Estratti 145 concetti chiave.</i></span>
      <div class="progress-bar-bg"><div class="progress-bar-fill" style="background-color: #4285F4; width: 100%;"></div></div>
    </div>
    <span class="msg-time">14:02</span>
  </div>
</div>
"""

# FASE 6: Claude 3.5 Processing (Inizio)
frame6 = frame5 + """
<div class="msg-row in">
  <div class="msg in" style="width: 100%;">
    <div class="status-box">
      <div class="status-header">
        <img src="https://www.google.com/s2/favicons?domain=claude.ai&sz=128" class="status-icon" style="background: #1e1e1e; border-radius: 6px;">
        <span style="color: #d4c5b9;">Claude 3.5 Sonnet</span>
      </div>
      <span style="font-size: 13px; color: #7f8991;">Sintesi partitura neurale... (45%)<br><i style="font-family: monospace; font-size: 10px; color: #d4c5b9;">> writing prompt logic...</i></span>
      <div class="progress-bar-bg"><div class="progress-bar-fill" style="background-color: #d4c5b9; width: 45%;"></div></div>
    </div>
    <span class="msg-time">14:02</span>
  </div>
</div>
"""

# FASE 7: Claude 3.5 Processing (Fine)
frame7 = frame5 + """
<div class="msg-row in">
  <div class="msg in" style="width: 100%;">
    <div class="status-box" style="border-color: rgba(212, 197, 185, 0.3); box-shadow: 0 0 10px rgba(212, 197, 185, 0.1);">
      <div class="status-header">
        <img src="https://www.google.com/s2/favicons?domain=claude.ai&sz=128" class="status-icon" style="background: #1e1e1e; border-radius: 6px;">
        <span style="color: #d4c5b9;">Claude 3.5 Sonnet</span>
      </div>
      <span style="font-size: 13px; color: #a4b3bf;">Sintesi audio completata! (100%)<br><i style="font-family: monospace; font-size: 10px; color: #d4c5b9;">> payload sent to Audio Engine.</i></span>
      <div class="progress-bar-bg"><div class="progress-bar-fill" style="background-color: #d4c5b9; width: 100%;"></div></div>
    </div>
    <span class="msg-time">14:03</span>
  </div>
</div>
"""

# FASE 8: Finale
frame8 = frame7 + """
<div class="msg-row in">
  <div class="msg in" style="width: 100%;">
    🎧 <b>Traccia Pronta!</b><br>
    <span style="font-size: 13px; color: #a4b3bf;">La tua soundtrack Ambient Cyberpunk basata sulla documentazione è stata mixata con successo.</span>
    
    <div class="audio-player">
      <div class="play-btn">
        <span style="color: white; font-size: 14px; margin-left: 3px;">▶</span>
      </div>
      <div style="flex: 1;">
        <div style="height: 5px; width: 100%; background: #17212b; border-radius: 3px; position: relative; overflow: hidden;">
           <div style="position: absolute; left: 0; top: 0; height: 100%; width: 35%; background: linear-gradient(90deg, #3390ec, #8B5CF6); border-radius: 3px;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 11px; color: #7f8991;">
           <span>0:45</span>
           <span>2:10</span>
        </div>
      </div>
    </div>
    <span class="msg-time">14:04</span>
  </div>
</div>
"""

# Creazione array di frame con ripetizioni per gestire le pause di lettura (storytelling timing)
# (Inizio) 1 x 5
# (Opzioni) 2 x 10
# (Scelta) 3 x 5
# (NB start) 4 x 6
# (NB end) 5 x 8
# (Claude start) 6 x 8
# (Claude end) 7 x 6
# (Finale) 8 x 15

storyline = [
    (frame1, 5),
    (frame2, 10),
    (frame3, 5),
    (frame4, 8),
    (frame5, 6),
    (frame6, 8),
    (frame7, 6),
    (frame8, 15)
]

print("Rendering True Story GIF...")
frames = []
for idx, (content, repeat) in enumerate(storyline):
    html_str = html_template.replace("{content}", content)
    filename = f"story_{idx}.png"
    filepath = os.path.join(hti.output_path, filename)
    hti.screenshot(html_str=html_str, save_as=filename)
    
    img = iio.imread(filepath)
    for _ in range(repeat):
        frames.append(img)

gif_path = "C:/podcastlab/docs/telegram_music_pipeline_HD.gif"
iio.imwrite(gif_path, frames, duration=150, loop=0)

size = os.path.getsize(gif_path)
print(f"✅ Fatto! GIF salvata in {gif_path} | Dimensioni: {size/1024:.2f} KB")

import shutil
try:
    shutil.rmtree(hti.output_path)
except:
    pass
