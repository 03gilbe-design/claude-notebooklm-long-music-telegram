import os
import math
import shutil
import imageio.v3 as iio
from html2image import Html2Image

hti = Html2Image(output_path='temp_hq_frames', size=(900, 650))
output_dir = r"C:\Users\Gilberto Bizzo\Downloads"
os.makedirs(output_dir, exist_ok=True)
os.makedirs('temp_hq_frames', exist_ok=True)

# Easing functions for buttery smooth animations
def ease_in_out_cubic(t):
    return 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2

def ease_out_elastic(t):
    if t == 0: return 0
    if t == 1: return 1
    c4 = (2 * math.pi) / 3
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def ease_in_out_quint(t):
    return 16 * t**5 if t < 0.5 else 1 - math.pow(-2 * t + 2, 5) / 2

def generate_grand_pipeline():
    print("Inizio rendering The Grand Pipeline (Alta Qualità / 30fps)...")
    html_template = """
    <html>
    <body style="margin: 0; background: #0f1219; width: 900px; height: 650px; display: flex; justify-content: center; align-items: center; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; position: relative; overflow: hidden;">
        
        <!-- Background Grid / Grid lines for high-tech aesthetic -->
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px); background-size: 30px 30px; opacity: {grid_op};"></div>

        <!-- FASE 1: INGESTION (NotebookLM) -->
        <div style="position: absolute; left: {nb_x}px; top: {nb_y}px; opacity: {nb_op}; transform: scale({nb_scale}); background: white; border-radius: 20px; width: 400px; height: 260px; box-shadow: 0 15px 40px rgba(66, 133, 244, {nb_glow}); display: flex; flex-direction: column; overflow: hidden; z-index: 10;">
            <div style="background: #4285F4; color: white; padding: 15px 25px; font-weight: 800; font-size: 22px; letter-spacing: 1px;">NotebookLM Engine</div>
            <div style="padding: 25px; flex: 1; display: flex; box-sizing: border-box; align-items: center;">
                <div style="width: 40%; position: relative;">
                    <!-- Data points floating in -->
                    <div style="position: absolute; left: {d1_x}px; top: 10px; width: 20px; height: 20px; background: #4285F4; border-radius: 50%; opacity: {d1_op};"></div>
                    <div style="position: absolute; left: {d2_x}px; top: 60px; width: 20px; height: 20px; background: #4285F4; border-radius: 50%; opacity: {d2_op};"></div>
                    <div style="position: absolute; left: {d3_x}px; top: 110px; width: 20px; height: 20px; background: #4285F4; border-radius: 50%; opacity: {d3_op};"></div>
                </div>
                <div style="width: 60%; display: flex; flex-direction: column; justify-content: center;">
                    <!-- Bars morphing -->
                    <div style="height: 14px; background: #e0e0e0; border-radius: 7px; margin-bottom: 18px; width: {t1_w}%;"></div>
                    <div style="height: 14px; background: #e0e0e0; border-radius: 7px; margin-bottom: 18px; width: {t2_w}%;"></div>
                    <div style="height: 14px; background: #e0e0e0; border-radius: 7px; margin-bottom: 18px; width: {t3_w}%;"></div>
                </div>
            </div>
        </div>

        <!-- FASE 2: CLAUDE SYNTHESIS -->
        <div style="position: absolute; left: {cl_x}px; top: {cl_y}px; opacity: {cl_op}; transform: scale({cl_scale}); background: #1a1b1e; border: 2px solid #d4c5b9; border-radius: 20px; width: 480px; height: 320px; box-shadow: 0 15px 50px rgba(212, 197, 185, {cl_glow}); display: flex; flex-direction: column; z-index: 15;">
            <div style="padding: 20px 25px; border-bottom: 1px solid rgba(212,197,185,0.2); color: #d4c5b9; font-size: 22px; font-weight: bold; letter-spacing: 2px;">Claude 3.5 Core</div>
            <div style="padding: 25px; color: #d4c5b9; font-family: monospace; font-size: 16px; line-height: 1.6;">
                {typing_text}<span style="display: inline-block; width: 12px; height: 20px; background: #d4c5b9; opacity: {cursor_op}; vertical-align: middle; margin-left: 6px;"></span>
            </div>
        </div>

        <!-- FASE 3: TELEGRAM DELIVERY -->
        <div style="position: absolute; left: {tg_x}px; top: {tg_y}px; opacity: {tg_op}; transform: scale({tg_scale}); background: #ffffff; border: 8px solid #2a2a2a; border-radius: 35px; width: 340px; height: 550px; box-shadow: 0 25px 60px rgba(51, 144, 236, {tg_glow}); display: flex; flex-direction: column; overflow: hidden; z-index: 20;">
            <div style="background: #3390ec; padding: 20px; color: white; text-align: center; font-weight: 800; font-size: 20px;">Telegram Interface</div>
            <div style="flex: 1; background: #e5ddd5; padding: 20px; display: flex; flex-direction: column; justify-content: flex-end; position: relative;">
                
                <!-- Incoming Data Ray from Claude -->
                <div style="position: absolute; top: {ray_y}px; left: {ray_x}px; width: 150px; height: 6px; background: linear-gradient(90deg, transparent, #3390ec); transform: rotate({ray_rot}deg); opacity: {ray_op}; border-radius: 3px;"></div>

                <!-- Chat bubble 1 (User) -->
                <div style="background: #e1ffc7; padding: 15px 20px; border-radius: 20px; border-bottom-right-radius: 4px; align-self: flex-end; margin-bottom: 15px; opacity: {bub1_op}; transform: translateY({bub1_y}px) scale({bub1_scale}); font-size: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    Generami una traccia musicale epica.
                    <div style="text-align: right; font-size: 12px; color: #6db345; margin-top: 5px;">14:00</div>
                </div>

                <!-- Chat bubble 2 (Audio File) -->
                <div style="background: #ffffff; padding: 15px; border-radius: 20px; border-bottom-left-radius: 4px; align-self: flex-start; opacity: {bub2_op}; transform: translateY({bub2_y}px) scale({bub2_scale}); width: 240px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; align-items: center;">
                    <div style="width: 45px; height: 45px; background: #3390ec; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 15px;">
                        <div style="width: 0; height: 0; border-top: 8px solid transparent; border-bottom: 8px solid transparent; border-left: 12px solid white; margin-left: 4px;"></div>
                    </div>
                    <div style="flex: 1;">
                        <div style="font-weight: bold; color: #3390ec; font-size: 15px;">epic_soundtrack.mp3</div>
                        <div style="height: 4px; background: #e0e0e0; width: 100%; border-radius: 2px; margin-top: 8px; position: relative;">
                            <div style="position: absolute; left: 0; top: 0; height: 100%; width: 40%; background: #3390ec; border-radius: 2px;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </body>
    </html>
    """
    
    # 3 FASI + transizioni (180 frame = 6 secondi a 30fps)
    num_frames = 180
    frames = []
    
    cl_text_full = "> Processing user query...\\n> Scanning NotebookLM corpus...\\n> Aligning entities...\\n> Sending logic payload to Audio Eng."
    
    for i in range(num_frames):
        p = i / (num_frames - 1)
        
        # Grid fade in
        grid_op = ease_in_out_cubic(min(1.0, p * 5)) * 0.5
        
        # --- FASE 1: NotebookLM (0.0 to 0.4) ---
        p1 = min(1.0, max(0, p / 0.35))
        e1 = ease_out_elastic(p1)
        
        nb_scale = 0.5 + e1 * 0.5 if p1 > 0 else 0.5
        nb_op = ease_in_out_cubic(min(1.0, p1 * 3))
        # Muovi via la card quando entra Claude
        p1_out = min(1.0, max(0, (p - 0.3) / 0.15))
        nb_x = 250 - ease_in_out_cubic(p1_out) * 600
        nb_y = 195
        nb_glow = ease_in_out_cubic(min(1.0, p1 * 2)) * 0.4
        
        d1_p = min(1.0, max(0, (p1 - 0.2) * 2))
        d2_p = min(1.0, max(0, (p1 - 0.3) * 2))
        d3_p = min(1.0, max(0, (p1 - 0.4) * 2))
        d1_x = -30 + ease_in_out_cubic(d1_p) * 190
        d2_x = -30 + ease_in_out_cubic(d2_p) * 190
        d3_x = -30 + ease_in_out_cubic(d3_p) * 190
        
        # Fade out elegante per i dots
        d1_op = max(0, 1.0 - max(0, (d1_p - 0.8) * 5)) if d1_p > 0 else 0
        d2_op = max(0, 1.0 - max(0, (d2_p - 0.8) * 5)) if d2_p > 0 else 0
        d3_op = max(0, 1.0 - max(0, (d3_p - 0.8) * 5)) if d3_p > 0 else 0
        
        t1_w = ease_in_out_cubic(min(1.0, max(0, (p1 - 0.4) * 2))) * 90
        t2_w = ease_in_out_cubic(min(1.0, max(0, (p1 - 0.5) * 2))) * 70
        t3_w = ease_in_out_cubic(min(1.0, max(0, (p1 - 0.6) * 2))) * 85
        
        # --- FASE 2: CLAUDE (0.3 to 0.7) ---
        p2 = min(1.0, max(0, (p - 0.3) / 0.35))
        e2 = ease_in_out_quint(p2)
        
        cl_scale = 0.8 + e2 * 0.2 if p2 > 0 else 0.8
        cl_op = ease_in_out_cubic(min(1.0, p2 * 3))
        p2_out = min(1.0, max(0, (p - 0.65) / 0.15))
        cl_x = 210 - ease_in_out_cubic(p2_out) * 600
        cl_y = 165
        cl_glow = ease_in_out_cubic(min(1.0, p2 * 2)) * 0.3
        
        typing_p = min(1.0, max(0, (p2 - 0.3) * 1.5))
        txt_len = int(typing_p * len(cl_text_full))
        typing_text = cl_text_full[:txt_len].replace("\\n", "<br><br>")
        cursor_op = 1 if (i // 5) % 2 == 0 else 0
        
        # --- FASE 3: TELEGRAM (0.6 to 1.0) ---
        p3 = min(1.0, max(0, (p - 0.6) / 0.4))
        e3 = ease_out_elastic(p3)
        
        tg_scale = 0.8 + e3 * 0.2 if p3 > 0 else 0.8
        tg_op = ease_in_out_cubic(min(1.0, p3 * 4))
        tg_x = 280
        tg_y = 50
        tg_glow = ease_in_out_cubic(min(1.0, p3 * 2)) * 0.4
        
        # Animazione messaggi interna a TG
        b1_p = min(1.0, max(0, (p3 - 0.2) * 3))
        bub1_scale = 0.5 + ease_out_elastic(b1_p) * 0.5
        bub1_op = ease_in_out_cubic(b1_p)
        bub1_y = 30 - ease_in_out_cubic(b1_p) * 30
        
        r_p = min(1.0, max(0, (p3 - 0.5) * 4))
        ray_x = -150 + ease_in_out_cubic(r_p) * 300
        ray_y = 200 + ease_in_out_cubic(r_p) * 100
        ray_rot = 35
        ray_op = 1.0 - max(0, (r_p - 0.7) * 3) if r_p > 0 else 0
        
        b2_p = min(1.0, max(0, (p3 - 0.7) * 3))
        bub2_scale = 0.5 + ease_out_elastic(b2_p) * 0.5
        bub2_op = ease_in_out_cubic(b2_p)
        bub2_y = 30 - ease_in_out_cubic(b2_p) * 30

        # Compila HTML
        html = html_template.format(
            grid_op=grid_op,
            nb_x=nb_x, nb_y=nb_y, nb_op=nb_op, nb_scale=nb_scale, nb_glow=nb_glow,
            d1_x=d1_x, d1_op=d1_op, d2_x=d2_x, d2_op=d2_op, d3_x=d3_x, d3_op=d3_op,
            t1_w=t1_w, t2_w=t2_w, t3_w=t3_w,
            cl_x=cl_x, cl_y=cl_y, cl_op=cl_op, cl_scale=cl_scale, cl_glow=cl_glow,
            typing_text=typing_text, cursor_op=cursor_op,
            tg_x=tg_x, tg_y=tg_y, tg_op=tg_op, tg_scale=tg_scale, tg_glow=tg_glow,
            bub1_op=bub1_op, bub1_y=bub1_y, bub1_scale=bub1_scale,
            ray_x=ray_x, ray_y=ray_y, ray_rot=ray_rot, ray_op=ray_op,
            bub2_op=bub2_op, bub2_y=bub2_y, bub2_scale=bub2_scale
        )
        
        filename = f"frame_{i:03d}.png"
        filepath = os.path.join('temp_hq_frames', filename)
        hti.screenshot(html_str=html, save_as=filename)
        frames.append(iio.imread(filepath))
        
    out_path = os.path.join(output_dir, "the_grand_pipeline.gif")
    # 33ms duration = ~30 FPS
    iio.imwrite(out_path, frames, duration=33, loop=0)
    print(f"Salvata la Mega-GIF Alta Qualità in: {out_path}")

if __name__ == "__main__":
    generate_grand_pipeline()
    try:
        shutil.rmtree('temp_hq_frames')
    except:
        pass
