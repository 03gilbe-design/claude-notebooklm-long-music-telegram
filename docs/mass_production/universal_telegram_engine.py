import os
import imageio.v3 as iio
from html2image import Html2Image
from collections import deque
import json

class TelegramEngine:
    def __init__(self, output_dir="C:/podcastlab/docs/mass_production", size=(420, 850)):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.hti = Html2Image(size=size)
        self.hti.output_path = os.path.join(self.output_dir, "temp_frames")
        os.makedirs(self.hti.output_path, exist_ok=True)
        
        self.html_template = """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
          body {
            margin: 0; padding: 0; background-color: #0e1621;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: #fff; width: 420px; height: 850px; display: flex; flex-direction: column; overflow: hidden;
          }
          .header {
            background-color: #17212b; padding: 12px 18px; font-weight: bold; font-size: 16px;
            display: flex; align-items: center; border-bottom: 1px solid #000; box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            z-index: 10;
          }
          .chat-container {
            flex: 1; padding: 15px; display: flex; flex-direction: column; gap: 12px;
            background-image: radial-gradient(circle at top right, #111a25, #0e1621);
            justify-content: flex-end; /* AUTO SCROLL TRICK */
          }
          .chat-messages {
            display: flex; flex-direction: column; gap: 12px; width: 100%;
          }
          .msg-row { display: flex; width: 100%; animation: slideIn 0.3s ease-out forwards; }
          @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
          
          .msg-row.in { justify-content: flex-start; }
          .msg-row.out { justify-content: flex-end; }
          .msg {
            max-width: 82%; padding: 10px 14px; border-radius: 14px; font-size: 15px;
            line-height: 1.45; position: relative; box-shadow: 0 1px 3px rgba(0,0,0,0.2);
          }
          .msg.in { background-color: #182533; border-bottom-left-radius: 4px; }
          .msg.out { background-color: #2b5278; border-bottom-right-radius: 4px; }
          .msg-time { font-size: 11px; color: rgba(255,255,255,0.5); float: right; margin-top: 6px; margin-left: 10px; }
          
          .input-area {
            background-color: #17212b; padding: 12px 15px; color: #7f8991; font-size: 15px;
            display: flex; align-items: center; box-shadow: 0 -1px 3px rgba(0,0,0,0.2); z-index: 10;
          }
          .input-area span { background-color: #242f3d; border-radius: 20px; padding: 12px 15px; flex: 1; }
          
          .inline-keyboard { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; width: 100%; }
          .inline-btn { background-color: #202b36; color: #3390ec; text-align: center; padding: 12px; border-radius: 8px; font-size: 14px; font-weight: bold; }
          
          .status-box { background-color: #0e1621; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 10px; margin-top: 8px; }
          .status-header { display: flex; align-items: center; margin-bottom: 8px; font-weight: 600; font-size: 14px; }
          .status-icon { width: 24px; height: 24px; border-radius: 4px; margin-right: 10px; background: #fff;}
          .progress-bar-bg { background-color: #17212b; border-radius: 4px; height: 6px; width: 100%; overflow: hidden; margin-top: 6px; }
          .progress-bar-fill { height: 100%; }
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
            <div class="chat-messages">
                {content}
            </div>
          </div>
          <div class="input-area"><span>Message...</span></div>
        </body>
        </html>
        """

    def render_story(self, story_name, sequence_of_messages):
        """
        sequence_of_messages: list of HTML strings representing messages.
        It renders the story progressively with auto-scroll (max 7 visible messages).
        """
        print(f"\\n--- RENDER: {story_name} ---")
        frames = []
        visible_messages = deque(maxlen=7) # Mantieni max 7 messaggi in coda per l'autoscroll
        frame_idx = 0
        
        for idx, msg_html in enumerate(sequence_of_messages):
            visible_messages.append(msg_html)
            
            # Uniamo i messaggi visibili
            joined_content = "\\n".join(visible_messages)
            html_str = self.html_template.replace("{content}", joined_content)
            
            # Screenshot di questo "stato"
            filename = f"{story_name}_{frame_idx}.png"
            filepath = os.path.join(self.hti.output_path, filename)
            self.hti.screenshot(html_str=html_str, save_as=filename)
            
            # Leggi e accoda (ripeti 10 volte per dare 1 secondo di pausa alla lettura di ogni step)
            img = iio.imread(filepath)
            for _ in range(12):  # circa 1.2 secondi a 100ms
                frames.append(img)
            
            frame_idx += 1
            
        out_path = os.path.join(self.output_dir, f"{story_name}.gif")
        iio.imwrite(out_path, frames, duration=100, loop=0)
        print(f"[OK] Completata: {out_path} ({len(frames)} frames totali)")

    def cleanup(self):
        import shutil
        try:
            shutil.rmtree(self.hti.output_path)
        except:
            pass
