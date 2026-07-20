import cv2
import numpy as np
from PIL import Image, ImageSequence
import os
import glob

def is_broken_placeholder(frame_rgb, debug=False):
    gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
    
    # White region > 235
    _, thresh = cv2.threshold(gray, 235, 255, cv2.THRESH_BINARY)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Check size (approx 80 to 200, making it a bit flexible)
        if 60 <= w <= 220 and 60 <= h <= 220:
            # Check aspect ratio
            if 0.7 <= w/h <= 1.3:
                area = cv2.contourArea(cnt)
                # Ensure it's mostly a solid block
                if area / (w*h) > 0.6:
                    # Get the bounding box in the original image
                    roi_gray = gray[y:y+h, x:x+w]
                    
                    # Check for gray border or little icon inside
                    # A pure white square is 255 mean. A placeholder has a gray border or an icon, so mean is slightly less than 255
                    # But it's mostly white, so mean > 220
                    mean_val = np.mean(roi_gray)
                    
                    if debug:
                        print(f"Candidate found: size={w}x{h}, area_ratio={area/(w*h):.2f}, mean_val={mean_val:.2f}")
                        
                    if mean_val > 210 and mean_val < 254.5:
                        # Found a broken placeholder
                        return True
                        
    return False

def check_gif(file_path):
    is_target = "3d_mixing_forge_icons.gif" in file_path
    try:
        gif = Image.open(file_path)
        for i, frame in enumerate(ImageSequence.Iterator(gif)):
            frame_rgb = frame.convert('RGB')
            frame_np = np.array(frame_rgb)
            if is_broken_placeholder(frame_np, debug=is_target):
                if is_target:
                    print(f"Target file broke at frame {i}")
                return True
        return False
    except Exception as e:
        if is_target:
            print(f"Error on target: {e}")
        return False

def main():
    base_dir = r"C:\podcastlab\docs\mass_production"
    gif_files = glob.glob(os.path.join(base_dir, "**", "*.gif"), recursive=True)
    
    target_file = r"C:\podcastlab\docs\mass_production\3D_Masterpieces\3d_mixing_forge_icons.gif"
    
    broken_count = 0
    total_files = len(gif_files)
    
    print(f"Total files: {total_files}")
    
    target_found = False
    
    for gif_file in gif_files:
        is_broken = check_gif(gif_file)
        if is_broken:
            broken_count += 1
            
        if os.path.normpath(gif_file) == os.path.normpath(target_file):
            print(f"Target file detected as broken: {is_broken}")
            target_found = True
            
    if not target_found:
        print("Target file not found in glob search. Checking directly...")
        if os.path.exists(target_file):
            is_broken = check_gif(target_file)
            print(f"Target file directly checked. Broken: {is_broken}")
            if is_broken:
                broken_count += 1
                total_files += 1
        else:
            print(f"Target file does not exist at path: {target_file}")
            
    print(f"\nResult: {broken_count} broken out of {total_files} total files.")

if __name__ == "__main__":
    main()
