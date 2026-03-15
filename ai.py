import sys
import math
import json
import time
import os
import pyautogui
import pytesseract
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

# Use msvcrt for non-blocking input on Windows
import msvcrt

# --- CONFIGURATION DEFAULTS ---
DEFAULT_SETTINGS = {
    "tesseract_path": r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    "ocr_timeout": 0.5,
    "click_delay": 0.8,
    "round_start_delay": 1.0,
    "continue_click_delay": 1.0,
    "rerun_timeout": 3.0
}

def load_config():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            # Merge with defaults to ensure all keys exist
            settings = DEFAULT_SETTINGS.copy()
            settings.update(config.get("settings", {}))
            config["settings"] = settings
            return config
    except FileNotFoundError:
        return {"regions": {}, "buttons": {}, "settings": DEFAULT_SETTINGS}

def setup_tesseract(tesseract_path):
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

def input_with_timeout(prompt, timeout=3.0, default='y'):
    """Waits for user input for a specified timeout on Windows."""
    print(f"{prompt} (Defaulting to '{default}' in {timeout}s): ", end="", flush=True)
    start_time = time.time()
    input_str = ""
    while True:
        if msvcrt.kbhit():
            char = msvcrt.getwche()
            if char in ('\r', '\n'):
                print() # Move to next line
                return input_str.strip() or default
            elif char == '\b': # Backspace
                if len(input_str) > 0:
                    input_str = input_str[:-1]
                    sys.stdout.write(' \b')
                    sys.stdout.flush()
            else:
                input_str += char
        
        if (time.time() - start_time) > timeout:
            print(f"\nTimed out. Using default: {default}")
            return default
        time.sleep(0.01)

def solve24(vals, steps=None):
    if steps is None:
        steps = []
    if len(vals) == 1:
        if math.isclose(vals[0][0], 24.0, abs_tol=1e-5):
            return steps
        return None
    for i in range(len(vals)):
        for j in range(len(vals)):
            if i == j: continue
            v_i, idx_i = vals[i]
            v_j, idx_j = vals[j]
            remaining = [vals[k] for k in range(len(vals)) if k != i and k != j]
            
            ops = [
                ('+', v_i + v_j, False), 
                ('-', v_j - v_i, True),  
                ('*', v_i * v_j, False)
            ]
            if abs(v_i) > 1e-8:
                ops.append(('/', v_j / v_i, True)) 
            
            for op_char, res_val, swap in ops:
                if res_val < -1e-5: continue 
                
                if swap:
                    new_step = (idx_j, op_char, idx_i, res_val, idx_i)
                    sol = solve24(remaining + [(res_val, idx_i)], steps + [new_step])
                else:
                    new_step = (idx_i, op_char, idx_j, res_val, idx_j)
                    sol = solve24(remaining + [(res_val, idx_j)], steps + [new_step])
                
                if sol: return sol
    return None

def get_numbers_from_screen(config):
    regions = config.get("regions", {})
    settings = config.get("settings", DEFAULT_SETTINGS)
    ocr_timeout = settings.get("ocr_timeout", 0.5)
    
    numbers = []
    print("Reading numbers from screen (Fast OCR with manual fallback)...")
    for key in ['num1', 'num2', 'num3', 'num4']:
        x, y, w, h = regions[key]
        img = pyautogui.screenshot(region=(x, y, w, h))
        
        # Fast Preprocessing
        img = img.convert('L')
        img = ImageOps.expand(img, border=10, fill='white')
        
        found_val = None
        start_time = time.time()
        
        for scale in [2, 1.5]:
            img_scaled = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
            img_proc = ImageEnhance.Contrast(img_scaled).enhance(2.0)
            
            for thresh in [128, 160]:
                img_bin = img_proc.point(lambda p: 255 if p > thresh else 0)
                if img_bin.load()[0, 0] < 128: img_bin = ImageOps.invert(img_bin)
                
                for psm in [10, 8]:
                    if time.time() - start_time > ocr_timeout: break 
                    
                    custom_config = f'--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789'
                    text = pytesseract.image_to_string(img_bin, config=custom_config).strip()
                    text = "".join([c for c in text if c.isdigit()])
                    if text:
                        try:
                            found_val = int(text)
                            break
                        except ValueError:
                            continue
                if found_val is not None or (time.time() - start_time > ocr_timeout): break
            if found_val is not None or (time.time() - start_time > ocr_timeout): break
        
        if found_val is not None:
            numbers.append(found_val)
            print(f"  Read {key}: {found_val}")
        else:
            print(f"  {key} OCR timed out or failed.")
            val = input(f"  Please enter value for {key}: ")
            try:
                numbers.append(int(val))
            except ValueError:
                print("Invalid integer.")
                return None

    print(f"Numbers to solve: {numbers}")
    ans = input("Proceed? ([y]/n or enter 4 new numbers): ").strip().lower()
    if ans == '' or ans == 'y':
        return numbers
    elif ans == 'n':
        return None
    elif len(ans.split()) == 4:
        try:
            return [int(x) for x in ans.split()]
        except ValueError:
            print("Invalid input.")
            return None
    
    return numbers

def execute_clicks(steps, config):
    buttons = config.get("buttons", {})
    settings = config.get("settings", DEFAULT_SETTINGS)
    click_delay = settings.get("click_delay", 0.8)
    
    print("Executing steps...")
    current_selected_idx = None
    
    for idx_a, op, idx_b, result, new_idx in steps:
        to_click = []
        if idx_a != current_selected_idx:
            to_click.append(f"num{idx_a + 1}")
        
        to_click.append(op)
        to_click.append(f"num{idx_b + 1}")
        
        for key in to_click:
            if key in buttons:
                x, y = buttons[key]
                pyautogui.click(x, y)
                print(f"  Click {key}")
                time.sleep(click_delay)
        
        current_selected_idx = new_idx

def run_bot_mode():
    config = load_config()
    settings = config.get("settings", DEFAULT_SETTINGS)
    setup_tesseract(settings.get("tesseract_path"))
        
    while True:
        print("\n--- NEW ROUND ---")
        round_start_delay = settings.get("round_start_delay", 1.0)
        print(f"Starting bot in {round_start_delay} second(s)...")
        time.sleep(round_start_delay)
        
        inputs = get_numbers_from_screen(config)
        if inputs:
            initial_vals = [(val, i) for i, val in enumerate(inputs)]
            steps = solve24(initial_vals)
            if steps:
                execute_clicks(steps, config)
                screen_w, screen_h = pyautogui.size()
                print("Clicking left side of screen to continue...")
                pyautogui.click(100, screen_h // 2)
                time.sleep(settings.get("continue_click_delay", 1.0))
            else:
                print("No solutions found.")
        
        rerun_timeout = settings.get("rerun_timeout", 3.0)
        cont = input_with_timeout("Run again for next numbers? ([y]/n)", timeout=rerun_timeout, default='y')
        if cont.lower() == 'n':
            break

def main():
    if '--bot' in sys.argv:
        run_bot_mode()
    elif len(sys.argv) == 5:
        config = load_config()
        try:
            inputs = [int(x) for x in sys.argv[1:5]]
            steps = solve24([(v, i) for i, v in enumerate(inputs)])
            if steps:
                for a, o, b, r, _ in steps: print(f"{inputs[a]} {o} {inputs[b]} = {int(r)}")
            else: print("No solutions.")
        except ValueError:
            print("Error: Please provide 4 integers.")
    else:
        print("Usage: python ai_win.py --bot  OR  python ai_win.py 1 2 3 4")

if __name__ == '__main__':
    main()
