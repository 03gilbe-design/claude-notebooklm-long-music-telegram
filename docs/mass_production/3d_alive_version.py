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

def ease_elastic(t):
    if t == 0 or t == 1: return t
    p = 0.3
    return math.pow(2, -10 * t) * math.sin((t - p / 4) * (2 * math.pi) / p) + 1

# Smorzatore per far tornare sempre alla forma base (1.0 per scale, 0 per rotate)
def spring_decay(t, start_val, target_val, freq=3, decay=5):
    if t < 0: return start_val
    if t > 1: return target_val
    return target_val + (start_val - target_val) * math.exp(-decay * t) * math.cos(freq * math.pi * 2 * t)

def create_3d_alive():
    print("Inizio rendering The 'Alive' 3D Version (Icons & Springs)...")
    hti = Html2Image(size=(800, 600))
    out_dir = "C:/podcastlab/docs/mass_production/3D_Masterpieces"
    os.makedirs(out_dir, exist_ok=True)
    temp_dir = os.path.join(out_dir, "temp_alive")
    hti.output_path = temp_dir
    os.makedirs(temp_dir, exist_ok=True)

    html_template = """
    <html>
    <body style="margin: 0; background: radial-gradient(circle, #1a1f2e 0%, #080a0f 100%); width: 800px; height: 600px; display: flex; justify-content: center; align-items: center; overflow: hidden; font-family: sans-serif;">
        <div style="width: 100%; height: 100%; transform-style: preserve-3d; perspective: 1200px;">
            <div style="position: absolute; width: 100%; height: 100%; transform-style: preserve-3d; transform: rotateX({rotX}deg) rotateY({rotY}deg) translateZ(-50px); transition: none;">
                
                <!-- NOTEBOOKLM (Che Spara) -->
                <div style="position: absolute; left: 100px; top: 250px; width: 100px; height: 100px; background: #fff; border-radius: {nb_radius}%; display: flex; justify-content: center; align-items: center; transform: translateZ({nb_z}px) scaleX({nb_sx}) scaleY({nb_sy}); box-shadow: 0 0 40px #4285F4;">
                    <img src="file:///C:/podcastlab/docs/assets/notebooklm_iconmark.svg" width="60" style="opacity: {nb_op};">
                </div>

                <!-- EPISODI MP3 (Proiettili vivi) -->
                <div style="position: absolute; left: {ep1_x}px; top: {ep1_y}px; width: 60px; height: 60px; background: #fff; border-radius: 15px; transform: translateZ({ep1_z}px) rotateZ({ep1_rz}deg) scaleX({ep1_sx}) scaleY({ep1_sy}); opacity: {ep_op}; box-shadow: 0 10px 20px rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;">
                    <img src="file:///C:/podcastlab/docs/assets/waveform_icon.png" width="40">
                </div>
                
                <div style="position: absolute; left: {ep2_x}px; top: {ep2_y}px; width: 60px; height: 60px; background: #fff; border-radius: 15px; transform: translateZ({ep2_z}px) rotateZ({ep2_rz}deg) scaleX({ep2_sx}) scaleY({ep2_sy}); opacity: {ep_op}; box-shadow: 0 10px 20px rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;">
                    <img src="file:///C:/podcastlab/docs/assets/waveform_icon.png" width="40">
                </div>
                
                <div style="position: absolute; left: {ep3_x}px; top: {ep3_y}px; width: 60px; height: 60px; background: #fff; border-radius: 15px; transform: translateZ({ep3_z}px) rotateZ({ep3_rz}deg) scaleX({ep3_sx}) scaleY({ep3_sy}); opacity: {ep_op}; box-shadow: 0 10px 20px rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;">
                    <img src="file:///C:/podcastlab/docs/assets/waveform_icon.png" width="40">
                </div>

                <!-- JINGLES (Intromissione Musicale - Apple Music) -->
                <div style="position: absolute; left: {j1_x}px; top: {j1_y}px; width: 50px; height: 50px; background: #fa243c; border-radius: 50%; transform: translateZ({j1_z}px) rotateZ({j1_rz}deg) scaleX({j_sx}) scaleY({j_sy}); opacity: {j_op}; box-shadow: 0 0 30px #fa243c; display: flex; align-items: center; justify-content: center;">
                    <img src="file:///C:/podcastlab/docs/assets/music_icon.png" width="35">
                </div>
                
                <div style="position: absolute; left: {j2_x}px; top: {j2_y}px; width: 50px; height: 50px; background: #fa243c; border-radius: 50%; transform: translateZ({j2_z}px) rotateZ({j2_rz}deg) scaleX({j_sx}) scaleY({j_sy}); opacity: {j_op}; box-shadow: 0 0 30px #fa243c; display: flex; align-items: center; justify-content: center;">
                    <img src="file:///C:/podcastlab/docs/assets/music_icon.png" width="35">
                </div>

                <!-- CLAUDE MIXER (Macchina di fusione che cattura tutto) -->
                <div style="position: absolute; left: {mix_x}px; top: {mix_y}px; width: 80px; height: 80px; background: #d4c5b9; border-radius: 20px; transform: translateZ({mix_z}px) scaleX({mix_sx}) scaleY({mix_sy}) rotateZ({mix_rz}deg); opacity: {mix_op}; box-shadow: 0 0 50px #d4c5b9; display: flex; justify-content: center; align-items: center;">
                    <img src="file:///C:/podcastlab/docs/assets/claude_icon.svg" width="50">
                </div>

                <!-- TELEGRAM (Ricevitore) -->
                <div style="position: absolute; left: 600px; top: {tg_y}px; width: 120px; height: 120px; background: transparent; transform: translateZ({tg_z}px) scaleX({tg_sx}) scaleY({tg_sy}); display: flex; justify-content: center; align-items: center; opacity: 1;">
                    <img src="file:///C:/podcastlab/docs/assets/telegram_icon.svg" width="120" style="filter: drop-shadow(0px 0px 20px rgba(51,144,236,0.8));">
                </div>

            </div>
        </div>
    </body>
    </html>
    """

    frames = []
    num_frames = 150
    
    for i in range(num_frames):
        p = i / float(num_frames - 1)
        
        rotX = 20
        rotY = 0

        # DEFAULT IDLE STATE (Forme non deformate)
        nb_sx, nb_sy, nb_z, nb_radius, nb_op = 1.0, 1.0, 0, 20, 1.0
        
        ep1_x, ep1_y, ep1_z, ep1_rz, ep1_sx, ep1_sy = 300, 270, 0, 0, 1.0, 1.0
        ep2_x, ep2_y, ep2_z, ep2_rz, ep2_sx, ep2_sy = 400, 270, 0, 0, 1.0, 1.0
        ep3_x, ep3_y, ep3_z, ep3_rz, ep3_sx, ep3_sy = 500, 270, 0, 0, 1.0, 1.0
        ep_op = 0

        j1_x, j1_y, j1_z, j1_rz = 355, 100, 0, 0
        j2_x, j2_y, j2_z, j2_rz = 455, 100, 0, 0
        j_sx, j_sy = 1.0, 1.0
        j_op = 0

        mix_x, mix_y, mix_z, mix_sx, mix_sy, mix_rz = 400, 260, 0, 0, 0, 0
        mix_op = 0

        tg_sx, tg_sy, tg_z, tg_y = 0.0, 0.0, 0, 240
        tg_x_pos = 600

        # FASE 1: SPUTO DA NOTEBOOKLM (0.0 - 0.25)
        if p < 0.25:
            p1 = p / 0.25
            
            # Anticipation & Sparo - Decadimento della pancia (torna a 1.0)
            if p1 < 0.3:
                a_p = p1 / 0.3
                nb_sx = 1.0 - a_p * 0.2
                nb_sy = 1.0 + a_p * 0.2
            else:
                s_p = (p1 - 0.3) / 0.7
                # Usa lo smorzatore per far tornare le dimensioni e la rotazione in posizione 1.0/0
                nb_sx = spring_decay(s_p, 1.4, 1.0, freq=2, decay=6)
                nb_sy = spring_decay(s_p, 0.7, 1.0, freq=2, decay=6)
                nb_radius = 50 - s_p * 30 # Torna quasi quadrato
                
                ep_op = 1
                sp_ease = ease_out_bounce(s_p)
                
                ep1_x = 100 + sp_ease * 170
                ep2_x = 100 + sp_ease * 270
                ep3_x = 100 + sp_ease * 370
                
                # I file volano stirati e poi TORNANO quadrati 1.0 (smorzamento)
                ep_stretch = spring_decay(s_p, 1.8, 1.0, freq=1.5, decay=5)
                ep1_sx, ep2_sx, ep3_sx = ep_stretch, ep_stretch, ep_stretch
                ep1_sy, ep2_sy, ep3_sy = 1/ep_stretch, 1/ep_stretch, 1/ep_stretch
                
        # FASE 2: INTROMISSIONE JINGLES E SPALLATA (0.25 - 0.5)
        elif p < 0.5:
            ep_op = 1
            ep1_x, ep2_x, ep3_x = 270, 370, 470
            
            p2 = (p - 0.25) / 0.25
            j_op = 1
            j_ease = ease_out_bounce(p2)
            
            j1_y = 50 + j_ease * 220
            j2_y = 50 + j_ease * 220
            j1_x = 320
            j2_x = 420
            
            # Stretch verticale e ritorno a 1.0
            j_stretch = spring_decay(p2, 2.0, 1.0, freq=2, decay=6)
            j_sy = j_stretch
            j_sx = 1/j_stretch
                
            # SPALLATA (Tilt and Return) sincronizzata col vero impatto al suolo
            if p2 > 0.6: # Climax Telegram inizia a nascere in sottofondo
                tg_sy = spring_decay((p2-0.6)/0.4, 1.2, 1.0, freq=2, decay=5)
                tg_sx = spring_decay((p2-0.6)/0.4, 0.8, 1.0, freq=2, decay=5)
            
            if j_ease > 0.8: # Solo quando il jingle tocca gli MP3 (sp_ease > 0.8) avviene l'impatto!
                imp_p = (j_ease - 0.8) / 0.2
                tlt = spring_decay(imp_p, 60, 0, freq=2, decay=7)
                shx = spring_decay(imp_p, 50, 0, freq=2, decay=7)
                ep1_x -= shx
                ep3_x += shx
                ep1_rz = -tlt
                ep3_rz = tlt

        # FASE 3: COMPRESSIONE CLAUDE (0.5 - 0.75)
        elif p < 0.75:
            p3 = (p - 0.5) / 0.25
            tg_sx, tg_sy = 1.0, 1.0
            
            # Stato persistito da fase 2: episodi e jingles restano a terra dove sono caduti
            ep1_x, ep2_x, ep3_x = 270, 370, 470
            j1_x, j2_x = 320, 420
            j1_y, j2_y = 270, 270
            if p3 < 0.3:
                # Claude nasce dal basso spinto dall'impatto dei jingle (causa -> effetto)
                ep_op = 1
                j_op = 1
                rise = ease_out_bounce(p3 / 0.3)
                mix_op = rise
                mix_y = 420 - rise * 160
                mix_sx = 0.6 + rise * 0.4
                mix_sy = 1.4 - rise * 0.4
            else:
                mix_op = 1
                mp3_p = (p3 - 0.3) / 0.7
                
                # Attrazione gravitazionale nel buco nero di Claude
                pull = mp3_p * mp3_p
                ep1_x = 270 + pull * 130
                ep3_x = 470 - pull * 130
                ep2_x = 370
                j1_x = 320 + pull * 80
                j2_x = 420 - pull * 80
                
                j1_y = 270
                j2_y = 270
                
                if mp3_p > 0.5: # Fusione graduale: parte lenta, accelera verso il centro
                    t_sh = (mp3_p - 0.5) / 0.5
                    shrink = 1.0 - t_sh * t_sh
                    ep1_sx, ep2_sx, ep3_sx = shrink, shrink, shrink
                    ep1_sy, ep2_sy, ep3_sy = shrink, shrink, shrink
                    j_sx, j_sy = shrink, shrink
                    ep_op = shrink
                    j_op = shrink
                    
                    # Claude ingrassa mangiandoli
                    mix_sx = spring_decay((mp3_p - 0.5)/0.5, 1.4, 1.0, freq=3, decay=5)
                    mix_sy = spring_decay((mp3_p - 0.5)/0.5, 0.7, 1.0, freq=3, decay=5)
                else:
                    ep_op = 1
                    j_op = 1
                    mix_sx = 1.0
                    mix_sy = 1.0

                mix_rz = spring_decay(mp3_p, 180, 0, freq=1, decay=4)
                
                # Claude si tira indietro prima di lanciare
                if mp3_p > 0.8:
                    ant = (mp3_p - 0.8) / 0.2
                    mix_x -= ant * 40
                    mix_rz = -ant * 20

        # FASE 4: TELEGRAM RICEVE (0.75 - 1.0)
        else:
            p4 = (p - 0.75) / 0.25
            mix_op = 1
            mix_x = 360
            
            fl = min(1.0, p4 * 1.5)
            # Claude lancia
            mix_x = 360 + ease_in_back(fl) * 250
            mix_rz = -20 + fl * 20
            mix_sx = spring_decay(fl, 1.8, 1.0, freq=1, decay=3)
            
            if p4 < 0.6:
                # Telegram aspetta (vibra o apre); Claude visibile per tutto il volo
                tg_sy = spring_decay(p4, 1.2, 1.0, freq=3, decay=6)
                tg_sx = spring_decay(p4, 0.8, 1.0, freq=3, decay=6)
            else:
                # Impatto: Claude entra in Telegram e solo ora sparisce
                mix_op = max(0.0, 1.0 - (p4 - 0.6) / 0.1)
                tg_p = (p4 - 0.6) / 0.4
                # Telegram riceve il colpo e s'ingrassa, poi torna normale
                tg_sx = spring_decay(tg_p, 1.4, 1.0, freq=2, decay=5)
                tg_sy = spring_decay(tg_p, 0.7, 1.0, freq=2, decay=5)
                # Il colpo sposta leggermente telegram a destra per l'inerzia e poi ritorna a 600
                tg_x_pos = 600 + spring_decay(tg_p, 50, 0, freq=1.5, decay=6)

        html = html_template.format(
            rotX=rotX, rotY=rotY,
            nb_sx=nb_sx, nb_sy=nb_sy, nb_z=nb_z, nb_radius=nb_radius, nb_op=nb_op,
            ep1_x=ep1_x, ep1_y=ep1_y, ep1_z=ep1_z, ep1_rz=ep1_rz, ep1_sx=ep1_sx, ep1_sy=ep1_sy,
            ep2_x=ep2_x, ep2_y=ep2_y, ep2_z=ep2_z, ep2_rz=ep2_rz, ep2_sx=ep2_sx, ep2_sy=ep2_sy,
            ep3_x=ep3_x, ep3_y=ep3_y, ep3_z=ep3_z, ep3_rz=ep3_rz, ep3_sx=ep3_sx, ep3_sy=ep3_sy,
            ep_op=ep_op,
            j1_x=j1_x, j1_y=j1_y, j1_z=j1_z, j1_rz=j1_rz, j2_x=j2_x, j2_y=j2_y, j2_z=j2_z, j2_rz=j2_rz, j_sx=j_sx, j_sy=j_sy, j_op=j_op,
            mix_x=mix_x, mix_y=mix_y, mix_z=mix_z, mix_sx=mix_sx, mix_sy=mix_sy, mix_rz=mix_rz, mix_op=mix_op,
            tg_y=tg_y, tg_z=tg_z, tg_sx=tg_sx, tg_sy=tg_sy
        )
        html = html.replace("left: 600px;", f"left: {tg_x_pos}px;")

        filename = f"alive_{i:03d}.png"
        filepath = os.path.join(temp_dir, filename)
        hti.screenshot(html_str=html, save_as=filename)
        frames.append(iio.imread(filepath))
        
    out_path = os.path.join(out_dir, "3d_alive_character.gif")
    iio.imwrite(out_path, frames, duration=40, loop=0)
    print(f"[OK] Completata The 3D Alive Character Version: {out_path}")

if __name__ == "__main__":
    create_3d_alive()
    try:
        shutil.rmtree("C:/podcastlab/docs/mass_production/3D_Masterpieces/temp_alive")
    except:
        pass
