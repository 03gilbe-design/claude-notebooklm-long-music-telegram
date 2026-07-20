import os

output_file = "C:/podcastlab/docs/mass_production/PIPELINE_COMPLETE_DUMP.txt"
files_to_dump = [
    "C:/podcastlab/docs/mass_production/embed_logos.py",
    "C:/podcastlab/docs/mass_production/universal_telegram_engine.py",
    "C:/podcastlab/docs/mass_production/generate_json_gifs.py",
    "C:/podcastlab/docs/mass_production/3d_forge_version.py",
    "C:/podcastlab/docs/mass_production/3d_highway_version.py",
    "C:/podcastlab/docs/mass_production/3d_alive_version.py",
    "C:/podcastlab/docs/mass_production/3d_circular_version.py"
]

with open(output_file, "w", encoding="utf-8") as out_f:
    out_f.write("=== PROGETTO PODCAST AUTOMATION 3D - DUMP PIPELINE COMPLETO ===\n")
    out_f.write("Questo file contiene tutti i codici sorgenti della pipeline.\n")
    out_f.write("Il sistema usa 'html2image' per renderizzare CSS 3D in Chromium e 'imageio' per comporre i frame.\n\n")
    
    for filepath in files_to_dump:
        if os.path.exists(filepath):
            filename = os.path.basename(filepath)
            out_f.write(f"\n=======================================================\n")
            out_f.write(f"FILE: {filename}\n")
            out_f.write(f"=======================================================\n\n")
            with open(filepath, "r", encoding="utf-8") as in_f:
                out_f.write(in_f.read())
            out_f.write("\n\n")

print(f"Dump completato in {output_file}")
