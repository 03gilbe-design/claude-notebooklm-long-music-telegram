import os
import json
import glob
from googletrans import Translator

def translate_all():
    translator = Translator()
    scripts_dir = "C:/podcastlab/docs/mass_production/scripts"
    json_files = glob.glob(os.path.join(scripts_dir, "*.json"))
    
    print(f"Translating {len(json_files)} JSON scripts to English...")
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                continue
                
        modified = False
        for step in data:
            if "text" in step and step["text"].strip():
                try:
                    res = translator.translate(step["text"], src='it', dest='en')
                    step["text"] = res.text
                    modified = True
                except Exception as e:
                    print(f"Translation error: {e}")
                    pass
        
        if modified:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Translated: {os.path.basename(file_path)}")

if __name__ == "__main__":
    translate_all()
    print("ALL JSON SCRIPTS TRANSLATED!")
