import os
import subprocess
import sys
import json
import time

def install_libraries():
    """Installs required libraries using pip."""
    print("=== Installing Required Libraries ===")
    required_libs = ["pyautogui", "pytesseract", "Pillow"]
    
    for lib in required_libs:
        print(f"Installing {lib}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
        except subprocess.CalledProcessError:
            print(f"Error: Failed to install {lib}. Please install it manually.")
            
    print("Libraries installation complete.\n")

def capture_coordinates():
    import pyautogui
    
    print("=== Make 24 Windows Setup ===")
    print("Move your mouse to the required position and wait for the beep/print.")
    print("Wait 3 seconds for each point.")
    print("-" * 30)

    config = {
        "regions": {},
        "buttons": {},
        "settings": {
            "tesseract_path": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            "ocr_timeout": 0.5,
            "click_delay": 0.8,
            "round_start_delay": 1.0,
            "continue_click_delay": 1.0,
            "rerun_timeout": 3.0
        }
    }

    # Helper to capture a region (Top-Left and Bottom-Right)
    def get_region(name):
        print(f"\n[Region: {name}]")
        print("1. Move to TOP-LEFT corner...")
        time.sleep(3)
        x1, y1 = pyautogui.position()
        print(f"   Captured: {x1}, {y1}")
        
        print("2. Move to BOTTOM-RIGHT corner...")
        time.sleep(3)
        x2, y2 = pyautogui.position()
        print(f"   Captured: {x2}, {y2}")
        
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        return [int(min(x1, x2)), int(min(y1, y2)), int(w), int(h)]

    # Helper to capture a single button point
    def get_point(name):
        print(f"\n[Button: {name}]")
        print("Move mouse to the center of the button...")
        time.sleep(3)
        x, y = pyautogui.position()
        print(f"   Captured: {x}, {y}")
        return [int(x), int(y)]

    # 1. Capture OCR Regions
    for i in range(1, 5):
        config["regions"][f"num{i}"] = get_region(f"Number {i}")

    # 2. Capture Click Buttons
    for i in range(1, 5):
        config["buttons"][f"num{i}"] = get_point(f"Number {i} Tile")

    for op in ['+', '-', '*', '/']:
        config["buttons"][op] = get_point(f"Operator '{op}'")

    # 3. Save Config
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    print("\n" + "="*30)
    print("SUCCESS: config.json created!")
    print("You can now run 'python ai_win.py --bot'")

if __name__ == "__main__":
    try:
        install_libraries()
        capture_coordinates()
    except KeyboardInterrupt:
        print("\nSetup cancelled.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        input("Press Enter to exit...")
