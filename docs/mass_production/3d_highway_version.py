import os
import math
import shutil
import imageio.v3 as iio
from html2image import Html2Image

def ease_in_out(t):
    return t * t * (3.0 - 2.0 * t)

def create_3d_highway():
    print("Inizio rendering The 3D Data Highway (Logos Only)...")
    hti = Html2Image(size=(800, 600))
    out_dir = "C:/podcastlab/docs/mass_production/3D_Masterpieces"
    os.makedirs(out_dir, exist_ok=True)
    temp_dir = os.path.join(out_dir, "temp_highway")
    hti.output_path = temp_dir
    os.makedirs(temp_dir, exist_ok=True)

    html_template = """
    <html>
    <body style="margin: 0; background: #0b101e; width: 800px; height: 600px; display: flex; justify-content: center; align-items: center; overflow: hidden; font-family: sans-serif;">
        <div style="width: 100%; height: 100%; transform-style: preserve-3d; perspective: 2000px;">
            <div style="position: absolute; width: 100%; height: 100%; transform-style: preserve-3d; transform: rotateX(60deg) rotateZ(45deg) scale(1.2) translateZ(-100px); transition: none;">
                
                <!-- Highway / Nastro Trasportatore -->
                <div style="position: absolute; left: 100px; top: -500px; width: 200px; height: 2000px; background-image: repeating-linear-gradient(0deg, rgba(66, 133, 244, 0.2) 0px, rgba(66, 133, 244, 0.2) 20px, transparent 20px, transparent 40px); background-size: 100% 40px; transform: translateY({belt_y}px); border-left: 5px solid #4285F4; border-right: 5px solid #4285F4; box-shadow: 0 0 40px rgba(66, 133, 244, 0.5);"></div>

                <!-- NOTEBOOKLM (Inizio nastro) -->
                <div style="position: absolute; left: 100px; top: -100px; width: 200px; height: 100px; background: #fff; box-shadow: 0 0 50px #4285F4; border-radius: 10px; display: flex; justify-content: center; align-items: center; transform: translateZ(50px);">
                    <img src="file:///C:/podcastlab/docs/assets/notebooklm_iconmark.svg" width="60">
                </div>

                <!-- FILE AUDIO (Scorrono sul nastro) -->
                <div style="position: absolute; left: 160px; top: {ep1_y}px; width: 80px; height: 80px; background: #fff; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.8); display: flex; justify-content: center; align-items: center; transform: translateZ({ep1_z}px); opacity: {ep_op};">
                    <img src="file:///C:/podcastlab/docs/assets/waveform_icon.png" width="50">
                </div>
                
                <div style="position: absolute; left: 160px; top: {ep2_y}px; width: 80px; height: 80px; background: #fff; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.8); display: flex; justify-content: center; align-items: center; transform: translateZ({ep2_z}px); opacity: {ep_op};">
                    <img src="file:///C:/podcastlab/docs/assets/waveform_icon.png" width="50">
                </div>
                
                <div style="position: absolute; left: 160px; top: {ep3_y}px; width: 80px; height: 80px; background: #fff; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.8); display: flex; justify-content: center; align-items: center; transform: translateZ({ep3_z}px); opacity: {ep_op};">
                    <img src="file:///C:/podcastlab/docs/assets/waveform_icon.png" width="50">
                </div>

                <!-- JINGLE ROCKETS (Arrivano dai lati come Emoji) -->
                <div style="position: absolute; left: {j1_x}px; top: {j1_y}px; width: 60px; height: 60px; transform: translateZ(20px); opacity: {j_op}; display: flex; justify-content: center; align-items: center; filter: drop-shadow(0 0 20px #8B5CF6);"><img src="file:///C:/podcastlab/docs/assets/music_icon.png" width="60"></div>
                <div style="position: absolute; left: {j2_x}px; top: {j2_y}px; width: 60px; height: 60px; transform: translateZ(20px); opacity: {j_op}; display: flex; justify-content: center; align-items: center; filter: drop-shadow(0 0 20px #8B5CF6);"><img src="file:///C:/podcastlab/docs/assets/music_icon.png" width="60"></div>

                <!-- LASER MIXER (Metà Nastro) -->
                <div style="position: absolute; left: 80px; top: 400px; width: 240px; height: 20px; background: #ff0055; box-shadow: 0 0 50px #ff0055; transform: translateZ(60px); opacity: {laser_op};"></div>
                <div style="position: absolute; left: 200px; top: 400px; width: 500px; height: 500px; background: radial-gradient(circle, rgba(255,0,85,0.5) 0%, transparent 70%); transform: translateZ({flash_z}px); opacity: {flash_op}; pointer-events: none;"></div>

                <!-- MEGAMIX FINALE (Claude Box) -->
                <div style="position: absolute; left: 130px; top: {final_y}px; width: 140px; height: 180px; background: #d4c5b9; border-radius: 20px; box-shadow: 0 0 40px #d4c5b9; display: flex; justify-content: center; align-items: center; transform: translateZ({final_z}px); opacity: {final_op};">
                    <img src="file:///C:/podcastlab/docs/assets/claude_icon.svg" width="80">
                </div>

                <!-- TELEGRAM RECEPTOR (Fine nastro) -->
                <div style="position: absolute; left: 100px; top: 800px; width: 200px; height: 200px; background: transparent; transform: translateZ({tg_z}px) scale({tg_scale}); display: flex; justify-content: center; align-items: center;">
                    <img src="file:///C:/podcastlab/docs/assets/telegram_icon.svg" width="200" style="filter: drop-shadow(0 0 50px #3390ec);">
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
        belt_y = (i * 10) % 40
        
        ep1_y, ep2_y, ep3_y = 0, 0, 0
        ep1_z, ep2_z, ep3_z = 20, 20, 20
        ep_op = 1.0
        
        j1_x, j1_y = 300, 0
        j2_x, j2_y = 300, 0
        j_op = 1.0
        
        laser_op = 0.5 + math.sin(i * 0.5) * 0.5
        flash_op = 0
        flash_z = 0
        
        final_y = 400
        final_z = 20
        final_op = 0
        
        tg_z = 10
        tg_scale = 1.0

        if p < 0.6:
            p1 = p / 0.6
            base_y = p1 * 500
            ep1_y = base_y + 120
            ep2_y = base_y
            ep3_y = base_y - 120
            
            j_p = min(1.0, max(0, p1 * 1.5))
            j1_x = 400 - ease_in_out(j_p) * 200
            j2_x = -200 + ease_in_out(j_p) * 330
            j1_y = base_y + 60
            j2_y = base_y - 60

        if p >= 0.5 and p < 0.7:
            p2 = (p - 0.5) / 0.2
            flash_op = math.sin(p2 * math.pi) * 0.8
            flash_z = 60
            laser_op = 1.0

        if p >= 0.6:
            ep_op = 0
            j_op = 0
            p3 = (p - 0.6) / 0.4
            
            final_op = 1.0
            final_y = 400 + ease_in_out(p3) * 400
            final_z = 20 + math.sin(p3 * math.pi) * 50
            
            if p3 > 0.8:
                tg_scale = 1.0 + math.sin((p3 - 0.8) * 5 * math.pi) * 0.3
                tg_z = 10 + math.sin((p3 - 0.8) * 5 * math.pi) * 50
                final_op = 1.0 - ((p3 - 0.8) * 5)

        html = html_template.format(
            belt_y=belt_y,
            ep1_y=ep1_y, ep1_z=ep1_z, ep2_y=ep2_y, ep2_z=ep2_z, ep3_y=ep3_y, ep3_z=ep3_z, ep_op=ep_op,
            j1_x=j1_x, j1_y=j1_y, j2_x=j2_x, j2_y=j2_y, j_op=j_op,
            laser_op=laser_op, flash_op=flash_op, flash_z=flash_z,
            final_y=final_y, final_z=final_z, final_op=max(0, final_op),
            tg_z=tg_z, tg_scale=tg_scale
        )
        
        filename = f"highway_{i:03d}.png"
        filepath = os.path.join(temp_dir, filename)
        hti.screenshot(html_str=html, save_as=filename)
        frames.append(iio.imread(filepath))
        
    out_path = os.path.join(out_dir, "3d_data_highway_icons.gif")
    iio.imwrite(out_path, frames, duration=40, loop=0)
    print(f"[OK] Completata The 3D Data Highway: {out_path}")

if __name__ == "__main__":
    create_3d_highway()
    try:
        shutil.rmtree("C:/podcastlab/docs/mass_production/3D_Masterpieces/temp_highway")
    except:
        pass
