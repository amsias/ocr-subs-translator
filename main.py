import requests
from plyer import notification
import pytesseract
from PIL import ImageGrab
import win32gui
from pynput import keyboard as pynput_keyboard
import pyautogui
import time
import sys
import os
import json

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Check if DeepSeek API key is set
DEEPSEEK_API_KEY = config.get("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "YOUR_DEEPSEEK_API_KEY_HERE":
    print("[ERROR] DEEPSEEK_API_KEY is not set in config.json. Please set it before running the script.")
    sys.exit(1)
CROP_BOX = tuple(config["crop_box"])


def get_ocr_subtitle():
    crop_box = CROP_BOX
    print(f"[INFO] Capturing screen region: {crop_box}")
    img = ImageGrab.grab(bbox=crop_box)
    img.save("vlc_subtitle_capture.png")
    print("[INFO] Saved captured image as vlc_subtitle_capture.png")
    print("[INFO] Running OCR...")
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(img, lang="eng", config=custom_config)
    print(f"[INFO] OCR result: '{text.strip()}'")
    return text.strip()

# The translate function can be any. Feel free to replace it with your own translation logic.
def translate(text):
    print(f"[INFO] Translating: '{text}'")
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    prompt = f"""
Eres un traductor profesional inglés-español especializado en diálogos de cine.
Traduce este texto manteniendo su carácter propio y adaptándolo al español latino.
Devuelve unicamente la traducción, sin explicaciones ni comentarios adicionales.
Texto: \"{text}\"
Traducción:"""
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 150
    }
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=20
        )
        if response.status_code == 200:
            translated = response.json()['choices'][0]['message']['content'].strip()
            print(f"[INFO] Translation result: '{translated}'")
            return translated
        else:
            print(f"[ERROR] Deepseek API error: {response.status_code}")
            print(f"[ERROR] Response text: {response.text}")
            print(f"[ERROR] Response content: {response.content}")
            print(f"[ERROR] Response headers: {response.headers}")
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        print(f"[ERROR] Connection error: {str(e)}")
        return f"Error de conexión: {str(e)}"

def show_notification(title, message):
    max_length = 250
    if len(message) > max_length:
        print(f"[WARN] Notification message too long ({len(message)}), truncating.")
        message = message[:max_length] + "..."
    print(f"[INFO] Showing notification: {title}: {message}")
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=5
        )
    except Exception as e:
        print(f"[ERROR] Notification failed: {e}")

def Logic():
    print("[INFO] Hotkey pressed. Starting subtitle translation...")
    subtitle = get_ocr_subtitle()
    if subtitle:
        translated = translate(subtitle)
        show_notification("Traducción:", f"{translated}")
    else:
        print("[WARN] No subtitle text detected.")

def On_button():
    Logic()

def calibrate_crop_box():
    print("[CALIBRATION] Move your mouse to the TOP-LEFT corner of the subtitle area and wait...")
    time.sleep(3)
    x1, y1 = pyautogui.position()
    print(f"[CALIBRATION] Top-left: ({x1}, {y1})")

    print("[CALIBRATION] Now move your mouse to the BOTTOM-RIGHT corner of the subtitle area and wait...")
    time.sleep(3)
    x2, y2 = pyautogui.position()
    print(f"[CALIBRATION] Bottom-right: ({x2}, {y2})")

    print(f"[CALIBRATION] Use crop_box = ({x1}, {y1}, {x2}, {y2}) in your script.")
    return (x1, y1, x2, y2)

# --- Main execution ---
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "calibrate":
        calibrate_crop_box()
        exit()
    hotkey = pynput_keyboard.GlobalHotKeys({
        '<ctrl>+<alt>+t': On_button
    })
    print("[INFO] Escuchando para traducir subtítulos... (Ctrl+Alt+T)")
    hotkey.start()
    hotkey.join()