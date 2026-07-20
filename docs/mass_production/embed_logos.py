import base64
import urllib.request
import os

def url_to_base64(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        content = response.read()
    mime = "image/svg+xml" if ".svg" in url else "image/png"
    if "favicons" in url: mime = "image/png"
    b64 = base64.b64encode(content).decode('utf-8')
    return f"data:{mime};base64,{b64}"

def file_to_base64(path):
    with open(path, "rb") as f:
        content = f.read()
    mime = "image/svg+xml" if path.endswith(".svg") else "image/png"
    b64 = base64.b64encode(content).decode('utf-8')
    return f"data:{mime};base64,{b64}"

try:
    nb_b64 = file_to_base64("C:/Users/Gilberto Bizzo/Downloads/notebooklm-color.svg")
    apple_music_b64 = url_to_base64("https://upload.wikimedia.org/wikipedia/commons/2/2a/Apple_Music_logo.svg")
    
    wave_svg = '<svg viewBox="0 0 24 24" fill="none" stroke="#3390ec" stroke-width="2" stroke-linecap="round" xmlns="http://www.w3.org/2000/svg"><path d="M12 3v18M8 8v8M16 6v12M4 11v2M20 10v4"/></svg>'
    wave_b64_str = base64.b64encode(wave_svg.encode('utf-8')).decode('utf-8')
    wave_b64 = f"data:image/svg+xml;base64,{wave_b64_str}"

    claude_b64 = url_to_base64("https://www.google.com/s2/favicons?domain=claude.ai&sz=128")
    tg_b64 = url_to_base64("https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg")

    files = [
        "C:/podcastlab/docs/mass_production/generate_json_gifs.py",
        "C:/podcastlab/docs/mass_production/3d_forge_version.py",
        "C:/podcastlab/docs/mass_production/3d_highway_version.py",
        "C:/podcastlab/docs/mass_production/3d_alive_version.py"
    ]

    for fpath in files:
        if not os.path.exists(fpath): continue
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        
        content = content.replace("file:///C:/Users/Gilberto%20Bizzo/Downloads/notebooklm-color.svg", nb_b64)
        content = content.replace("https://raw.githubusercontent.com/tabler/tabler-icons/master/icons/waveform.svg", wave_b64)
        content = content.replace("https://upload.wikimedia.org/wikipedia/commons/2/2a/Apple_Music_logo.svg", apple_music_b64)
        content = content.replace("https://upload.wikimedia.org/wikipedia/commons/e/e7/Podcasts_%28iOS%29.svg", apple_music_b64)
        content = content.replace("https://www.google.com/s2/favicons?domain=claude.ai&sz=128", claude_b64)
        content = content.replace("https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg", tg_b64)

        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)

    print("SUCCESS: Base64 Injection Complete!")
except Exception as e:
    print(f"ERROR: {str(e)}")
