import os
import imageio.v3 as iio
from html2image import Html2Image

hti = Html2Image(size=(400, 900))
hti.output_path = "C:/podcastlab/docs"

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
    height: 900px;
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
<div class="msg-row out">
  <div class="msg out">
    The rise of Generative AI
    <span class="msg-time">10:00</span>
  </div>
</div>
"""

frame2 = frame1 + """
<div class="msg-row in" style="margin-top: 10px;">
  <div style="max-width: 85%; width: 100%;">
    <div class="msg in" style="max-width: 100%; box-sizing: border-box;">
      Topic set. Pick an option from the menu:
      <span class="msg-time">10:00</span>
    </div>
    <div class="inline-keyboard">
      <div class="inline-btn">🎙️ Generate episodes</div>
      <div class="inline-btn">🔍 Web research</div>
      <div class="inline-btn">🎵 Pick music</div>
    </div>
  </div>
</div>
"""

frame3 = frame2 + """
<div class="msg-row out" style="margin-top: 10px;">
  <div class="msg out">
    🎵 Music: Hybrid
    <span class="msg-time">10:01</span>
  </div>
</div>
"""

frame4 = frame3 + """
<div class="msg-row in" style="margin-top: 10px;">
  <div class="msg in" style="width: 100%;">
    🔍 <b>Web Research Phase</b><br>
    <span style="font-size: 12px; color: #7f8991;">Analyzing sources (45%)</span>
    <div style="background-color: #0e1621; border-radius: 5px; height: 8px; margin-top: 8px; width: 100%; overflow: hidden;">
      <div style="background-color: #3390ec; height: 100%; width: 45%;"></div>
    </div>
    <span class="msg-time">10:02</span>
  </div>
</div>
"""

frame5 = frame4 + """
<div class="msg-row in" style="margin-top: 10px;">
  <div class="msg in" style="width: 100%;">
    🎙️ <b>Podcast Generation</b><br>
    <span style="font-size: 12px; color: #7f8991;">Writing episode 2 of 3 (66%)</span>
    <div style="background-color: #0e1621; border-radius: 5px; height: 8px; margin-top: 8px; width: 100%; overflow: hidden;">
      <div style="background-color: #3390ec; height: 100%; width: 66%;"></div>
    </div>
    <span class="msg-time">10:05</span>
  </div>
</div>
"""

frame6 = frame5 + """
<div class="msg-row in" style="margin-top: 10px;">
  <div class="msg in" style="width: 100%;">
    ✅ <b>Processing Complete!</b><br><br>
    📁 Dataset: <i>dataset_ai_gen.json</i><br>
    🎧 Mixed podcast (with hybrid music):
    <div style="display:flex; align-items:center; background-color:#242f3d; padding:10px; border-radius:8px; margin-top:8px;">
      <div style="width:36px; height:36px; background-color:#3390ec; border-radius:50%; display:flex; justify-content:center; align-items:center; margin-right:10px;">
        <span style="color:white; font-size:16px;">▶</span>
      </div>
      <div style="flex:1;">
        <div style="background-color:#3390ec; height:4px; width:100%; border-radius:2px;"></div>
      </div>
      <div style="margin-left:10px; font-size:12px;">15:20</div>
    </div>
    <span class="msg-time">10:08</span>
  </div>
</div>
"""

frames_html = [frame1, frame2, frame3, frame4, frame5, frame6]
filenames = []

for i, content in enumerate(frames_html):
    html_content = html_template.replace("{content}", content)
    out_name = f"bot_flow_frame_{i}.png"
    out_path = os.path.join("C:/podcastlab/docs", out_name)
    filenames.append(out_path)
    # The output path is handled by hti.output_path. 
    # BUT hti.screenshot takes output_path + save_as.
    hti.screenshot(html_str=html_content, save_as=out_name)

images = []
for file in filenames:
    images.append(iio.imread(file))

# Duplicate last frame so it pauses
for _ in range(2):
    images.append(images[-1])

gif_path = "C:/podcastlab/docs/bot_flow.gif"
iio.imwrite(gif_path, images, duration=1500, loop=0)

size = os.path.getsize(gif_path)
print(f"GIF created: {gif_path}, Size: {size / 1024:.2f} KB")

# Cleanup intermediate files
for file in filenames:
    try:
        os.remove(file)
    except Exception as e:
        print("Failed to remove", file, e)
