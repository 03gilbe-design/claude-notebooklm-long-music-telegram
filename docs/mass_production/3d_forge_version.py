import os
import math
import shutil
import imageio.v3 as iio
from html2image import Html2Image

def ease_in_out(t):
    return t * t * (3.0 - 2.0 * t)

def create_3d_forge():
    print("Inizio rendering The 3D Mixing Forge (Logos Only)...")
    hti = Html2Image(size=(800, 600))
    out_dir = "C:/podcastlab/docs/mass_production/3D_Masterpieces"
    os.makedirs(out_dir, exist_ok=True)
    temp_dir = os.path.join(out_dir, "temp_forge")
    hti.output_path = temp_dir
    os.makedirs(temp_dir, exist_ok=True)

    html_template = """
    <html>
    <body style="margin: 0; background: radial-gradient(circle, #1a1a24 0%, #050508 100%); width: 800px; height: 600px; display: flex; justify-content: center; align-items: center; overflow: hidden; font-family: sans-serif;">
        <!-- Il Mondo 3D -->
        <div style="width: 100%; height: 100%; transform-style: preserve-3d; perspective: 1000px;">
            <div style="position: absolute; width: 100%; height: 100%; transform-style: preserve-3d; transform: rotateX({rotX}deg) rotateY({rotY}deg) scale({scale}); transition: none;">
                
                <!-- Pista / Grid -->
                <div style="position: absolute; left: -400px; top: 100px; width: 1600px; height: 1600px; background-image: linear-gradient(rgba(51,144,236,0.1) 2px, transparent 2px), linear-gradient(90deg, rgba(51,144,236,0.1) 2px, transparent 2px); background-size: 50px 50px; transform: rotateX(90deg) translateZ(-150px); opacity: {grid_op};"></div>

                <!-- NOTEBOOKLM SERVER (Sinistra) -->
                <div style="position: absolute; left: 150px; top: 200px; width: 120px; height: 120px; background: rgba(255,255,255,1); border-radius: 20px; box-shadow: 0 0 50px rgba(66, 133, 244, 0.6); display: flex; justify-content: center; align-items: center; transform: translateZ(-200px) rotateY(15deg);">
                    <img src="file:///C:/podcastlab/docs/assets/notebooklm_iconmark.svg" width="100">
                </div>

                <!-- TELEGRAM (Destra) -->
                <div style="position: absolute; left: 600px; top: 220px; width: 120px; height: 120px; background: transparent; display: flex; justify-content: center; align-items: center; transform: translateZ(100px) rotateY(-20deg) scale({tg_scale}); opacity: {tg_op};">
                    <img src="file:///C:/podcastlab/docs/assets/telegram_icon.svg" width="120" style="filter: drop-shadow(0 0 40px #3390ec);">
                </div>

                <!-- FILE AUDIO EPISODI -->
                <div style="position: absolute; left: {ep1_x}px; top: {ep1_y}px; width: 60px; height: 60px; background: #fff; border-radius: 12px; display: flex; justify-content: center; align-items: center; transform: translateZ({ep1_z}px) rotateY({ep1_ry}deg) rotateX({ep_rx}deg); opacity: {ep_op}; box-shadow: 0 5px 15px rgba(255,255,255,0.2);">
                    <img src='file:///C:/podcastlab/docs/assets/waveform_icon.png' width="40">
                </div>
                
                <div style="position: absolute; left: {ep2_x}px; top: {ep2_y}px; width: 60px; height: 60px; background: #fff; border-radius: 12px; display: flex; justify-content: center; align-items: center; transform: translateZ({ep2_z}px) rotateY({ep2_ry}deg) rotateX({ep_rx}deg); opacity: {ep_op}; box-shadow: 0 5px 15px rgba(255,255,255,0.2);">
                    <img src='file:///C:/podcastlab/docs/assets/waveform_icon.png' width="40">
                </div>
                
                <div style="position: absolute; left: {ep3_x}px; top: {ep3_y}px; width: 60px; height: 60px; background: #fff; border-radius: 12px; display: flex; justify-content: center; align-items: center; transform: translateZ({ep3_z}px) rotateY({ep3_ry}deg) rotateX({ep_rx}deg); opacity: {ep_op}; box-shadow: 0 5px 15px rgba(255,255,255,0.2);">
                    <img src='file:///C:/podcastlab/docs/assets/waveform_icon.png' width="40">
                </div>

                <!-- JINGLES (Stacchi) -->
                <div style="position: absolute; left: {j1_x}px; top: {j1_y}px; width: 50px; height: 50px; background: transparent; transform: translateZ({j1_z}px) rotateX({ep_rx}deg); opacity: {j_op}; display: flex; justify-content: center; align-items: center; filter: drop-shadow(0 0 10px #8B5CF6);"><img src='file:///C:/podcastlab/docs/assets/music_icon.png' width="50"></div>
                <div style="position: absolute; left: {j2_x}px; top: {j2_y}px; width: 50px; height: 50px; background: transparent; transform: translateZ({j2_z}px) rotateX({ep_rx}deg); opacity: {j_op}; display: flex; justify-content: center; align-items: center; filter: drop-shadow(0 0 10px #FF2A54);"><img src='file:///C:/podcastlab/docs/assets/music_icon.png' width="50"></div>

                <!-- MUSIC SOTTOFONDO -->
                <div style="position: absolute; left: {bg_x}px; top: {bg_y}px; width: {bg_w}px; height: 15px; background: rgba(51,144,236,0.6); border-radius: 10px; transform: translateZ({bg_z}px) rotateX({ep_rx}deg); opacity: {bg_op}; box-shadow: 0 0 30px rgba(51,144,236,1);"></div>
                
                <!-- UNIONE FINALE EFFETTO (Claude) -->
                <div style="position: absolute; left: {final_x}px; top: {final_y}px; width: {final_w}px; height: {final_h}px; background: #d4c5b9; border-radius: 20px; transform: translateZ({final_z}px) rotateX({final_rx}deg); opacity: {final_op}; box-shadow: 0 0 50px #d4c5b9; display: flex; align-items: center; justify-content: center;">
                    <img src='file:///C:/podcastlab/docs/assets/claude_icon.svg' width="50" style="opacity: {claude_op};">
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    frames = []
    num_frames = 120
    
    for i in range(num_frames):
        p = i / float(num_frames - 1)
        
        # CAMERA ANIMATION
        rotX = 10 + ease_in_out(min(1.0, p * 1.5)) * 25
        rotY = 30 - ease_in_out(p) * 60
        scale = 1.0 + ease_in_out(min(1.0, p * 2)) * 0.2
        grid_op = 1.0 - ease_in_out(max(0, (p - 0.8)*5))

        # FASE 1: SPUTATI DA NOTEBOOK LM (p: 0.0 - 0.3)
        p1 = min(1.0, max(0, p / 0.25))
        e1 = ease_in_out(p1)
        ep_op = 1.0 if p1 > 0 and p < 0.7 else 0.0
        ep_rx = 0 if p < 0.7 else 90
        
        ep1_x = 220 + e1 * 50
        ep1_y = 250 - math.sin(e1 * math.pi) * 50
        ep1_z = -150 + e1 * 150
        ep1_ry = e1 * 360
        
        ep2_x = 220 + e1 * 150
        ep2_y = 250 - math.sin(e1 * math.pi) * 80
        ep2_z = -150 + e1 * 150
        ep2_ry = e1 * 360
        
        ep3_x = 220 + e1 * 250
        ep3_y = 250 - math.sin(e1 * math.pi) * 110
        ep3_z = -150 + e1 * 150
        ep3_ry = e1 * 360

        # FASE 2: JINGLES SI BUTTANO IN MEZZO (p: 0.25 - 0.45)
        p2 = min(1.0, max(0, (p - 0.25) / 0.2))
        e2 = math.pow(p2, 2)
        j_op = 1.0 if p2 > 0 and p < 0.7 else 0.0
        
        j1_x = 330
        j1_y = -100 + e2 * 350
        j1_z = 0
        
        j2_x = 430
        j2_y = -100 + e2 * 350
        j2_z = 0

        # FASE 3: SOTTOFONDO MUSICALE SI STENDE SOTTO (p: 0.45 - 0.6)
        p3 = min(1.0, max(0, (p - 0.45) / 0.15))
        bg_op = p3 if p < 0.7 else 0.0
        bg_x = 260
        bg_y = 310
        bg_z = 0
        bg_w = p3 * 250

        # FASE 4: COMPRESSIONE (CLAUDE) E FUSIONE (p: 0.6 - 0.8)
        p4 = min(1.0, max(0, (p - 0.6) / 0.2))
        e4 = ease_in_out(p4)
        
        ep1_x = 270 + e4 * 60
        ep3_x = 470 - e4 * 60
        
        final_op = 1.0 if p > 0.75 else 0.0
        claude_op = 1.0 if p > 0.75 else 0.0
        final_w = 250 - e4 * 150
        final_h = 50 + e4 * 50
        final_x = 320 + e4 * 80
        final_y = 250
        final_z = 0
        final_rx = e4 * 360

        if p > 0.7:
            ep_op = 0
            j_op = 0
            bg_op = 0

        # FASE 5: LANCIO VERSO TELEGRAM (p: 0.8 - 1.0)
        p5 = min(1.0, max(0, (p - 0.8) / 0.2))
        e5 = ease_in_out(p5)
        
        tg_op = min(1.0, max(0, (p - 0.6) * 3))
        tg_scale = 0.5 + tg_op * 0.5
        
        final_x = final_x + e5 * 200
        final_y = final_y - e5 * 30
        final_z = final_z + e5 * 100
        
        if p5 > 0.9:
            final_op = 1.0 - ((p5 - 0.9) * 10)
            tg_scale = 1.0 + math.sin((p5 - 0.9) * 10 * math.pi) * 0.2

        html = html_template.format(
            rotX=rotX, rotY=rotY, scale=scale, grid_op=grid_op,
            ep1_x=ep1_x, ep1_y=ep1_y, ep1_z=ep1_z, ep1_ry=ep1_ry, ep_rx=ep_rx, ep_op=ep_op,
            ep2_x=ep2_x, ep2_y=ep2_y, ep2_z=ep2_z, ep2_ry=ep2_ry,
            ep3_x=ep3_x, ep3_y=ep3_y, ep3_z=ep3_z, ep3_ry=ep3_ry,
            j1_x=j1_x, j1_y=j1_y, j1_z=j1_z, j_op=j_op,
            j2_x=j2_x, j2_y=j2_y, j2_z=j2_z,
            bg_x=bg_x, bg_y=bg_y, bg_z=bg_z, bg_w=bg_w, bg_op=bg_op,
            final_x=final_x, final_y=final_y, final_z=final_z, final_rx=final_rx, final_w=final_w, final_h=final_h, final_op=final_op, claude_op=claude_op,
            tg_op=tg_op, tg_scale=tg_scale
        )
        
        filename = f"forge_{i:03d}.png"
        filepath = os.path.join(temp_dir, filename)
        hti.screenshot(html_str=html, save_as=filename)
        frames.append(iio.imread(filepath))
        
    out_path = os.path.join(out_dir, "3d_mixing_forge_icons.gif")
    iio.imwrite(out_path, frames, duration=40, loop=0)
    print(f"[OK] Completata The 3D Mixing Forge: {out_path}")

if __name__ == "__main__":
    create_3d_forge()
    try:
        shutil.rmtree("C:/podcastlab/docs/mass_production/3D_Masterpieces/temp_forge")
    except:
        pass
