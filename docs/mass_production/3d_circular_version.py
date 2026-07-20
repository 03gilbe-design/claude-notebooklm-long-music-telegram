import os
import math
import shutil
import imageio.v3 as iio
from html2image import Html2Image

def ease_in_back(t):
    s = 1.70158
    return t * t * ((s + 1) * t - s)

def ease_out_back(t):
    s = 1.70158
    t -= 1
    return (t * t * ((s + 1) * t + s) + 1)

def ease_out_bounce(t):
    n1 = 7.5625
    d1 = 2.75
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375

def spring_decay(t, start_val, target_val, freq=3, decay=5):
    if t < 0: return start_val
    if t > 1: return target_val
    return target_val + (start_val - target_val) * math.exp(-decay * t) * math.cos(freq * math.pi * 2 * t)

def create_circular_3d():
    print("Inizio rendering The 3D Circular Version (Roaming Camera)...")
    hti = Html2Image(size=(800, 600))
    out_dir = "C:/podcastlab/docs/mass_production/3D_Masterpieces"
    os.makedirs(out_dir, exist_ok=True)
    temp_dir = os.path.join(out_dir, "temp_circular")
    hti.output_path = temp_dir
    os.makedirs(temp_dir, exist_ok=True)

    html_template = """
    <html>
    <body style="margin: 0; background: radial-gradient(circle at center, #111a26 0%, #06090f 100%); width: 800px; height: 600px; display: flex; justify-content: center; align-items: center; overflow: hidden; font-family: sans-serif;">
        <!-- ROAMING CAMERA -->
        <div style="width: 100%; height: 100%; transform-style: preserve-3d; perspective: 1000px;">
            <div style="position: absolute; width: 100%; height: 100%; transform-style: preserve-3d; transform: rotateX({rotX}deg) rotateY({rotY}deg) translateZ({camZ}px); transition: none;">
                
                <!-- TELEGRAM (Il punto di partenza e arrivo in Basso) -->
                <div style="position: absolute; left: 340px; top: {tg_y}px; width: 120px; height: 120px; background: transparent; transform: translateZ({tg_z}px) scaleX({tg_sx}) scaleY({tg_sy}); display: flex; justify-content: center; align-items: center; opacity: 1;">
                    <img src="file:///C:/podcastlab/docs/assets/telegram_icon.svg" width="120" style="filter: drop-shadow(0px 0px 20px rgba(51,144,236,0.8));">
                </div>

                <!-- NOTEBOOKLM (La Sorgente API in Alto) -->
                <div style="position: absolute; left: 350px; top: 50px; width: 100px; height: 100px; background: #fff; border-radius: {nb_radius}%; display: flex; justify-content: center; align-items: center; transform: translateZ({nb_z}px) scaleX({nb_sx}) scaleY({nb_sy}); box-shadow: 0 0 40px #4285F4; opacity: {nb_op};">
                    <img src="file:///C:/podcastlab/docs/assets/notebooklm_iconmark.svg" width="60">
                </div>

                <!-- 3 TRACCE VOCALI PODCAST -->
                <div style="position: absolute; left: {ep1_x}px; top: {ep1_y}px; width: 60px; height: 60px; background: #fff; border-radius: 15px; transform: translateZ({ep1_z}px) rotateZ({ep1_rz}deg) scaleX({ep1_sx}) scaleY({ep1_sy}); opacity: {ep_op}; box-shadow: 0 10px 20px rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;">
                    <img src="file:///C:/podcastlab/docs/assets/waveform_icon.png" width="40">
                </div>
                <div style="position: absolute; left: {ep2_x}px; top: {ep2_y}px; width: 60px; height: 60px; background: #fff; border-radius: 15px; transform: translateZ({ep2_z}px) rotateZ({ep2_rz}deg) scaleX({ep2_sx}) scaleY({ep2_sy}); opacity: {ep_op}; box-shadow: 0 10px 20px rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;">
                    <img src="file:///C:/podcastlab/docs/assets/waveform_icon.png" width="40">
                </div>
                <div style="position: absolute; left: {ep3_x}px; top: {ep3_y}px; width: 60px; height: 60px; background: #fff; border-radius: 15px; transform: translateZ({ep3_z}px) rotateZ({ep3_rz}deg) scaleX({ep3_sx}) scaleY({ep3_sy}); opacity: {ep_op}; box-shadow: 0 10px 20px rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;">
                    <img src="file:///C:/podcastlab/docs/assets/waveform_icon.png" width="40">
                </div>

                <!-- CLAUDE MIXER (Al Centro) -->
                <div style="position: absolute; left: {mix_x}px; top: {mix_y}px; width: 80px; height: 80px; background: #d4c5b9; border-radius: {mix_rad}px; transform: translateZ({mix_z}px) scaleX({mix_sx}) scaleY({mix_sy}) rotateZ({mix_rz}deg); opacity: {mix_op}; box-shadow: 0 0 50px #d4c5b9; display: flex; justify-content: center; align-items: center;">
                    <img src="file:///C:/podcastlab/docs/assets/claude_icon.svg" width="50">
                </div>

                <!-- DYNAMIC LASER / DATA BEAM -->
                <div style="position: absolute; left: {beam_x}px; top: {beam_y}px; width: 10px; height: {beam_h}px; background: #3390ec; opacity: {beam_op}; box-shadow: 0 0 20px #3390ec; border-radius: 10px; transform: translateZ({beam_z}px);"></div>

            </div>
        </div>
    </body>
    </html>
    """

    frames = []
    num_frames = 180
    
    for i in range(num_frames):
        p = i / float(num_frames - 1)
        
        # CONTINUOUS ROAMING CAMERA 3D
        rotX = 30 + math.sin(p * math.pi * 2) * 20
        rotY = math.cos(p * math.pi * 2) * 20
        camZ = -50 + math.sin(p * math.pi * 4) * 30

        # DEFAULT IDLE
        tg_sx, tg_sy, tg_z, tg_y = 1.0, 1.0, 0, 420
        nb_sx, nb_sy, nb_z, nb_radius, nb_op = 1.0, 1.0, 0, 20, 1.0
        mix_x, mix_y, mix_z, mix_sx, mix_sy, mix_rz, mix_op, mix_rad = 360, 230, 0, 1.0, 1.0, 0, 0, 20
        ep_op = 0
        ep1_x, ep1_y, ep1_z, ep1_rz, ep1_sx, ep1_sy = 370, 50, 0, 0, 1.0, 1.0
        ep2_x, ep2_y, ep2_z, ep2_rz, ep2_sx, ep2_sy = 370, 50, 0, 0, 1.0, 1.0
        ep3_x, ep3_y, ep3_z, ep3_rz, ep3_sx, ep3_sy = 370, 50, 0, 0, 1.0, 1.0
        beam_x, beam_y, beam_h, beam_op, beam_z = 395, 230, 0, 0, 0

        # FASE 1: TELEGRAM CHIEDE API AL NOTEBOOK (0 - 0.25)
        if p < 0.25:
            p1 = p / 0.25
            mix_op = 0
            
            # Telegram spara un raggio in alto (Anticipazione giu, scatto su)
            if p1 < 0.3:
                tg_sy = 1.0 - p1
                tg_sx = 1.0 + p1
            else:
                sp1 = (p1 - 0.3) / 0.7
                tg_sy = spring_decay(sp1, 1.8, 1.0, 2, 5)
                tg_sx = spring_decay(sp1, 0.5, 1.0, 2, 5)
                
                beam_op = 1
                beam_h = 250 * sp1
                beam_y = 420 - beam_h
                
                # Se il raggio tocca NotebookLM (circa al frame sp1=0.8)
                if sp1 > 0.8:
                    imp1 = (sp1 - 0.8) / 0.2
                    nb_sy = spring_decay(imp1, 0.5, 1.0, 3, 6)
                    nb_sx = spring_decay(imp1, 1.5, 1.0, 3, 6)
                    nb_radius = 50

        # FASE 2: NOTEBOOK LM SPUTA 3 FILE (0.25 - 0.5)
        elif p < 0.5:
            p2 = (p - 0.25) / 0.25
            ep_op = 1
            
            if p2 < 0.3:
                nb_sy = 1.0 + p2
                nb_sx = 1.0 - p2
            else:
                sp2 = (p2 - 0.3) / 0.7
                nb_sy = spring_decay(sp2, 0.5, 1.0, 2, 5)
                nb_sx = spring_decay(sp2, 1.5, 1.0, 2, 5)
                
                sp_ease = ease_out_bounce(sp2)
                ep1_y = 50 + sp_ease * 150
                ep2_y = 50 + sp_ease * 150
                ep3_y = 50 + sp_ease * 150
                ep1_x = 370 - sp_ease * 100
                ep3_x = 370 + sp_ease * 100

        # FASE 3: CLAUDE NASCE DAL BASSO E RICEVE LE TRACCE (0.5 - 0.75)
        elif p < 0.75:
            p3 = (p - 0.5) / 0.25
            ep_op = 1
            
            # CLIMAX DI CLAUDE (Appare dal nulla crescendo)
            if p3 < 0.4:
                mix_op = p3 / 0.4
                mix_sx = ease_out_bounce(p3 / 0.4)
                mix_sy = mix_sx
            else:
                mix_op = 1
                sp3 = (p3 - 0.4) / 0.6
                mix_sx = 1.0
                mix_sy = 1.0
                
                # Le tracce si buttano dentro Claude e fondono (riducendo scala a 0)
                pull = sp3 * sp3
                ep1_x = 270 + pull * 90
                ep2_x = 370
                ep3_x = 470 - pull * 90
                ep1_y = 200 + pull * 30
                ep2_y = 200 + pull * 30
                ep3_y = 200 + pull * 30
                
                # Le tracce shrinkano dentro Claude e spariscono
                if sp3 > 0.6:
                    shrink = 1.0 - ((sp3 - 0.6) / 0.4)
                    ep1_sx, ep2_sx, ep3_sx = shrink, shrink, shrink
                    ep1_sy, ep2_sy, ep3_sy = shrink, shrink, shrink
                    mix_sx = spring_decay((sp3 - 0.6)/0.4, 1.3, 1.0, 2, 6)
                    mix_sy = spring_decay((sp3 - 0.6)/0.4, 1.3, 1.0, 2, 6)

        # FASE 4: CLAUDE SPARA A TELEGRAM (0.75 - 1.0)
        else:
            p4 = (p - 0.75) / 0.25
            mix_op = 1
            
            # Claude si carica all'indietro
            if p4 < 0.3:
                mix_y = 230 - p4 * 100
            else:
                sp4 = (p4 - 0.3) / 0.7
                mix_y = 230 - 30 + ease_in_back(sp4) * 220
                
                # Telegram riceve il file master
                if sp4 > 0.8:
                    imp4 = (sp4 - 0.8) / 0.2
                    tg_sy = spring_decay(imp4, 0.4, 1.0, 3, 6)
                    tg_sx = spring_decay(imp4, 1.6, 1.0, 3, 6)
                    mix_op = 1.0 - imp4 # claude sparisce nel mix
                    
        html = html_template.format(
            rotX=rotX, rotY=rotY, camZ=camZ,
            nb_sx=nb_sx, nb_sy=nb_sy, nb_z=nb_z, nb_radius=nb_radius, nb_op=nb_op,
            ep1_x=ep1_x, ep1_y=ep1_y, ep1_z=ep1_z, ep1_rz=ep1_rz, ep1_sx=ep1_sx, ep1_sy=ep1_sy,
            ep2_x=ep2_x, ep2_y=ep2_y, ep2_z=ep2_z, ep2_rz=ep2_rz, ep2_sx=ep2_sx, ep2_sy=ep2_sy,
            ep3_x=ep3_x, ep3_y=ep3_y, ep3_z=ep3_z, ep3_rz=ep3_rz, ep3_sx=ep3_sx, ep3_sy=ep3_sy,
            ep_op=ep_op,
            mix_x=mix_x, mix_y=mix_y, mix_z=mix_z, mix_sx=mix_sx, mix_sy=mix_sy, mix_rz=mix_rz, mix_op=mix_op, mix_rad=mix_rad,
            beam_x=beam_x, beam_y=beam_y, beam_h=beam_h, beam_op=beam_op, beam_z=beam_z,
            tg_y=tg_y, tg_z=tg_z, tg_sx=tg_sx, tg_sy=tg_sy
        )
        
        filename = f"frame_{i:03d}.png"
        frame_path = os.path.join(temp_dir, filename)
        hti.screenshot(html_str=html, save_as=filename)
        frames.append(iio.imread(frame_path))

    out_path = os.path.join(out_dir, "3d_circular_pipeline.gif")
    iio.imwrite(out_path, frames, duration=40, loop=0)
    print(f"[OK] Completata The 3D Circular Pipeline: {out_path}")

if __name__ == "__main__":
    create_circular_3d()
