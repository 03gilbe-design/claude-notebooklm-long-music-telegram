import os
import imageio.v3 as iio
from html2image import Html2Image

hti = Html2Image(size=(400, 600))
# On Windows, sometimes hti needs explicit browser executable path, but we'll try default.

html_template = """
<!DOCTYPE html>
<html>
<head>
<style>
  body {
    margin: 0;
    padding: 0;
    background-color: #0e1621;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #fff;
    width: 400px;
    height: 600px;
    display: flex;
    flex-direction: column;
  }
  .header {
    background-color: #17212b;
    padding: 10px 15px;
    font-weight: bold;
    font-size: 16px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid #000;
  }
  .chat-container {
    flex: 1;
    padding: 15px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .msg-row {
    display: flex;
    width: 100%;
  }
  .msg-row.in {
    justify-content: flex-start;
  }
  .msg-row.out {
    justify-content: flex-end;
  }
  .msg {
    max-width: 80%;
    padding: 8px 12px;
    border-radius: 12px;
    font-size: 15px;
    line-height: 1.4;
    position: relative;
    box-shadow: 0 1px 2px rgba(0,0,0,0.15);
  }
  .msg.in {
    background-color: #182533;
    border-bottom-left-radius: 4px;
  }
  .msg.out {
    background-color: #2b5278;
    border-bottom-right-radius: 4px;
  }
  .msg-time {
    font-size: 11px;
    color: rgba(255,255,255,0.5);
    float: right;
    margin-top: 4px;
    margin-left: 8px;
  }
  .inline-keyboard {
    margin-top: 5px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    width: 100%;
  }
  .inline-btn {
    background-color: #202b36;
    color: #3390ec;
    text-align: center;
    padding: 10px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: bold;
  }
  .input-area {
    background-color: #17212b;
    padding: 10px 15px;
    color: #7f8991;
    font-size: 15px;
    display: flex;
    align-items: center;
  }
  .input-area span {
    background-color: #242f3d;
    border-radius: 20px;
    padding: 10px 15px;
    flex: 1;
  }
</style>
</head>
<body>
  <div class="header">
    <div style="width: 35px; height: 35px; background: #3390ec; border-radius: 50%; margin-right: 10px; display:flex; align-items:center; justify-content:center;">B</div>
    <div style="line-height: 1.2;">Podcast Bot<br><span style="font-size: 12px; color: #7f8991; font-weight: normal;">bot</span></div>
  </div>
  <div class="chat-container">
    {content}
  </div>
  <div class="input-area">
    <span>Message...</span>
  </div>
</body>
</html>
"""

frame1 = """
<div class="msg-row in">
  <div class="msg in">
    Benvenuto! Scegli un topic di cui vuoi parlare nel prossimo podcast.
    <span class="msg-time">12:30</span>
  </div>
</div>
"""

frame2 = """
<div class="msg-row in">
  <div style="max-width: 85%;">
    <div class="msg in" style="max-width: 100%; box-sizing: border-box;">
      Benvenuto! Scegli un topic di cui vuoi parlare nel prossimo podcast.
      <span class="msg-time">12:30</span>
    </div>
    <div class="inline-keyboard">
      <div class="inline-btn">🚀 AI & Tech</div>
      <div class="inline-btn">💡 Imprenditoria</div>
      <div class="inline-btn">🎧 Podcasting Tips</div>
    </div>
  </div>
</div>
"""

frame3 = frame2 + """
<div class="msg-row out" style="margin-top: 10px;">
  <div class="msg out">
    🚀 AI & Tech
    <span class="msg-time">12:31</span>
  </div>
</div>
<div class="msg-row in" style="margin-top: 10px;">
  <div class="msg in">
    Ottima scelta! Generazione dello script in corso... ⏳
    <span class="msg-time">12:31</span>
  </div>
</div>
"""

frames_html = [frame1, frame2, frame3]
filenames = []

for i, content in enumerate(frames_html):
    html_content = html_template.replace("{content}", content)
    out_name = f"frame_{i}.png"
    filenames.append(out_name)
    hti.screenshot(html_str=html_content, save_as=out_name)

# Create GIF
images = []
for file in filenames:
    images.append(iio.imread(file))

# Duplicate last frame so it pauses
images.append(images[-1])
images.append(images[-1])

gif_path = "telegram_mock_test.gif"
iio.imwrite(gif_path, images, duration=1500, loop=0) # duration is in ms

# Print file size
size = os.path.getsize(gif_path)
print(f"GIF created: {gif_path}, Size: {size / 1024:.2f} KB")

# Cleanup intermediate files
for file in filenames:
    try:
        os.remove(file)
    except:
        pass
