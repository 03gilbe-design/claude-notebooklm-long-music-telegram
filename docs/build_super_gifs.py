import os
import imageio.v3 as iio
from html2image import Html2Image
import shutil

hti = Html2Image(output_path='temp_frames', size=(800, 600))

output_dir = r"C:\Users\Gilberto Bizzo\Downloads"
os.makedirs(output_dir, exist_ok=True)
os.makedirs('temp_frames', exist_ok=True)

# 1) notebook_ingestion.gif
def make_notebook_ingestion():
    print("Generating notebook_ingestion.gif...")
    html_template = """
    <html>
    <body style="margin: 0; background: #121212; width: 800px; height: 600px; display: flex; justify-content: center; align-items: center; font-family: sans-serif;">
        <div style="background: white; border-radius: 20px; width: 500px; height: 300px; position: relative; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.8);">
            <!-- Header -->
            <div style="background: #4285F4; color: white; padding: 15px 20px; font-weight: bold; font-size: 20px;">
                NotebookLM
            </div>
            
            <div style="padding: 20px; display: flex; height: calc(100% - 55px); box-sizing: border-box;">
                <!-- Left: Dots area -->
                <div style="width: 50%; height: 100%; position: relative;">
                    <div style="position: absolute; left: {dot_x}px; top: 40px; width: 16px; height: 16px; background: #4285F4; border-radius: 50%; opacity: {dot_op};"></div>
                    <div style="position: absolute; left: {dot_x2}px; top: 90px; width: 16px; height: 16px; background: #4285F4; border-radius: 50%; opacity: {dot_op2};"></div>
                    <div style="position: absolute; left: {dot_x3}px; top: 140px; width: 16px; height: 16px; background: #4285F4; border-radius: 50%; opacity: {dot_op3};"></div>
                </div>
                
                <!-- Right: Text area -->
                <div style="width: 50%; padding-left: 20px; display: flex; flex-direction: column; justify-content: center; box-sizing: border-box;">
                    <div style="height: 12px; background: #e0e0e0; border-radius: 6px; margin-bottom: 15px; width: {text_w1}%;"></div>
                    <div style="height: 12px; background: #e0e0e0; border-radius: 6px; margin-bottom: 15px; width: {text_w2}%;"></div>
                    <div style="height: 12px; background: #e0e0e0; border-radius: 6px; margin-bottom: 15px; width: {text_w3}%;"></div>
                    <div style="height: 12px; background: #e0e0e0; border-radius: 6px; margin-bottom: 15px; width: {text_w4}%;"></div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    frames = []
    num_frames = 30
    for i in range(num_frames):
        progress = i / (num_frames - 1)
        
        d1 = min(1.0, progress * 1.5)
        dot_x = -20 + d1 * 220
        dot_op = max(0, 1.0 - max(0, d1 - 0.8) * 5)
        
        d2 = min(1.0, max(0, progress - 0.2) * 1.5)
        dot_x2 = -20 + d2 * 220
        dot_op2 = max(0, 1.0 - max(0, d2 - 0.8) * 5)
        
        d3 = min(1.0, max(0, progress - 0.4) * 1.5)
        dot_x3 = -20 + d3 * 220
        dot_op3 = max(0, 1.0 - max(0, d3 - 0.8) * 5)
        
        tw1 = min(100, max(0, (progress - 0.3) * 200))
        tw2 = min(85, max(0, (progress - 0.5) * 200))
        tw3 = min(90, max(0, (progress - 0.7) * 200))
        tw4 = min(60, max(0, (progress - 0.8) * 200))
        
        html = html_template.format(dot_x=dot_x, dot_op=dot_op, 
                                    dot_x2=dot_x2, dot_op2=dot_op2, 
                                    dot_x3=dot_x3, dot_op3=dot_op3,
                                    text_w1=tw1, text_w2=tw2, text_w3=tw3, text_w4=tw4)
        
        filename = f"notebook_{i}.png"
        filepath = os.path.join('temp_frames', filename)
        hti.screenshot(html_str=html, save_as=filename)
        frames.append(iio.imread(filepath))
        
    out_path = os.path.join(output_dir, "notebook_ingestion.gif")
    iio.imwrite(out_path, frames, duration=100, loop=0)

# 2) claude_brain.gif
def make_claude_brain():
    print("Generating claude_brain.gif...")
    html_template = """
    <html>
    <body style="margin: 0; background: #0f0f0f; width: 800px; height: 600px; display: flex; justify-content: center; align-items: center; font-family: monospace;">
        <div style="background: #1e1e1e; border: 2px solid #d4c5b9; border-radius: 12px; width: 450px; height: {card_h}px; position: relative; overflow: hidden; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 0 20px rgba(212, 197, 185, 0.2);">
            <div style="color: #d4c5b9; font-size: 26px; font-weight: bold; margin-bottom: {title_mb}px; opacity: {title_op};">Claude Brain</div>
            <div style="color: #d4c5b9; font-size: 16px; width: 80%; text-align: left; line-height: 1.5; display: {text_disp};">
                {typing_text}<span style="display: inline-block; width: 10px; height: 16px; background: #d4c5b9; opacity: {cursor_op}; vertical-align: middle; margin-left: 5px;"></span>
            </div>
        </div>
    </body>
    </html>
    """
    
    full_text = "> Analyzing user prompt...\\n> Extracting key entities...\\n> Formulating response strategy...\\n> Synthesizing precise data architecture."
    
    frames = []
    num_frames = 40
    for i in range(num_frames):
        progress = i / (num_frames - 1)
        
        card_h = 80 + progress * 220
        title_mb = progress * 20
        title_op = min(1.0, progress * 4)
        
        text_disp = "block" if progress > 0.1 else "none"
        text_len = int(max(0, progress - 0.1) / 0.9 * len(full_text))
        current_text = full_text[:text_len].replace("\\n", "<br>")
        
        cursor_op = 1 if i % 4 < 2 else 0
        
        html = html_template.format(card_h=card_h, title_mb=title_mb, title_op=title_op, 
                                    text_disp=text_disp, typing_text=current_text, cursor_op=cursor_op)
        
        filename = f"claude_{i}.png"
        filepath = os.path.join('temp_frames', filename)
        hti.screenshot(html_str=html, save_as=filename)
        frames.append(iio.imread(filepath))
        
    out_path = os.path.join(output_dir, "claude_brain.gif")
    iio.imwrite(out_path, frames, duration=100, loop=0)

# 3) telegram_orchestration.gif
def make_telegram_orchestration():
    print("Generating telegram_orchestration.gif...")
    html_template = """
    <html>
    <body style="margin: 0; background: #1a1a1a; width: 800px; height: 600px; display: flex; justify-content: center; align-items: center; font-family: sans-serif; position: relative;">
        
        <!-- Left capsule (Claude) -->
        <div style="position: absolute; left: {claude_x}px; top: 275px; background: #d4c5b9; padding: 12px 25px; border-radius: 25px; font-weight: bold; font-size: 18px; color: #121212; z-index: 2; box-shadow: 0 4px 15px rgba(212,197,185,0.3);">Claude</div>
        
        <!-- Right capsule (NotebookLM) -->
        <div style="position: absolute; right: {notebook_x}px; top: 275px; background: #4285F4; padding: 12px 25px; border-radius: 25px; font-weight: bold; font-size: 18px; color: white; z-index: 2; box-shadow: 0 4px 15px rgba(66,133,244,0.3);">NotebookLM</div>
        
        <!-- Left ray -->
        <div style="position: absolute; left: 160px; top: 295px; width: {ray_l_w}px; height: 4px; background: #d4c5b9; z-index: 1; box-shadow: 0 0 10px #d4c5b9; opacity: {ray_op}; border-radius: 2px;"></div>
        
        <!-- Right ray -->
        <div style="position: absolute; right: 180px; top: 295px; width: {ray_r_w}px; height: 4px; background: #4285F4; z-index: 1; box-shadow: 0 0 10px #4285F4; opacity: {ray_op}; border-radius: 2px;"></div>
        
        <!-- Telegram Phone Mockup -->
        <div style="background: #ffffff; border: 6px solid #2a2a2a; border-radius: 30px; width: 320px; height: 500px; position: relative; overflow: hidden; display: flex; flex-direction: column; z-index: 3; box-shadow: 0 15px 40px rgba(0,0,0,0.5);">
            <div style="background: #3390ec; padding: 15px; color: white; text-align: center; font-weight: bold; font-size: 18px; letter-spacing: 0.5px;">Telegram Bot</div>
            <div style="flex: 1; background: #e5ddd5; padding: 15px; display: flex; flex-direction: column; justify-content: flex-end; position: relative;">
                
                <!-- Incoming rays data representation inside chat -->
                <div style="position: absolute; top: 50%; left: 0; width: 100%; height: 2px; display: flex; justify-content: space-between; opacity: {inner_ray_op};">
                    <div style="width: 30%; height: 100%; background: #d4c5b9; transform: translateX({inner_l_x}px); border-radius: 2px;"></div>
                    <div style="width: 30%; height: 100%; background: #4285F4; transform: translateX({inner_r_x}px); border-radius: 2px;"></div>
                </div>

                <!-- Final bubble -->
                <div style="background: #ffffff; padding: 12px 18px; border-radius: 18px; border-bottom-left-radius: 4px; margin-top: 10px; max-width: 80%; opacity: {bubble_op}; transform: translateY({bubble_y}px); font-size: 15px; color: #000; box-shadow: 0 1px 2px rgba(0,0,0,0.15);">
                    Data Orchestration Complete. Ready for next step!
                    <div style="text-align: right; font-size: 11px; color: #888; margin-top: 4px;">13:15</div>
                </div>
            </div>
        </div>
        
    </body>
    </html>
    """
    
    frames = []
    num_frames = 45
    for i in range(num_frames):
        progress = i / (num_frames - 1)
        
        claude_x = 30 + min(1.0, progress * 2) * 20
        notebook_x = 30 + min(1.0, progress * 2) * 20
        
        ray_op = 1.0 if progress < 0.6 else max(0, 1.0 - (progress - 0.6) * 5)
        ray_l_w = min(110, max(0, (progress - 0.1) * 300))
        ray_r_w = min(100, max(0, (progress - 0.1) * 300))
        
        # Smooth interpolation for inner_ray_op
        if progress < 0.3:
            inner_ray_op = 0.0
        elif progress < 0.4:
            inner_ray_op = (progress - 0.3) * 10
        elif progress <= 0.6:
            inner_ray_op = 1.0
        elif progress < 0.7:
            inner_ray_op = 1.0 - (progress - 0.6) * 10
        else:
            inner_ray_op = 0.0
            
        inner_l_x = min(150, (progress - 0.4) * 400)
        inner_r_x = max(-150, -(progress - 0.4) * 400)
        
        b_prog = max(0, progress - 0.7) * 3.33
        bubble_op = min(1.0, b_prog)
        bubble_y = 20 - bubble_op * 20
        
        html = html_template.format(
            claude_x=claude_x, notebook_x=notebook_x,
            ray_op=ray_op, ray_l_w=ray_l_w, ray_r_w=ray_r_w,
            inner_ray_op=inner_ray_op, inner_l_x=inner_l_x, inner_r_x=inner_r_x,
            bubble_op=bubble_op, bubble_y=bubble_y
        )
        
        filename = f"telegram_{i}.png"
        filepath = os.path.join('temp_frames', filename)
        hti.screenshot(html_str=html, save_as=filename)
        frames.append(iio.imread(filepath))
        
    out_path = os.path.join(output_dir, "telegram_orchestration.gif")
    iio.imwrite(out_path, frames, duration=100, loop=0)

if __name__ == "__main__":
    make_notebook_ingestion()
    make_claude_brain()
    make_telegram_orchestration()
    
    # Cleanup temp frames
    try:
        shutil.rmtree('temp_frames')
    except:
        pass
    print("All GIFs generated successfully!")
