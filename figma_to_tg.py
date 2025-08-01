import os
import requests
import time
from datetime import datetime
from config import FRAME_CONFIGS

# === НАСТРОЙКИ ===
FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHANNEL_ID")

HISTORY_DIR = "history"
os.makedirs(HISTORY_DIR, exist_ok=True)

def get_frame_text(file_id, node_id):
    url = f"https://api.figma.com/v1/files/{file_id}/nodes?ids={node_id}"
    headers = {"X-Figma-Token": FIGMA_TOKEN}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        node = data["nodes"][node_id]["document"]
        return extract_text_with_newlines(node)
    except Exception as e:
        print(f"[ERROR] Ошибка получения текста для {file_id}:{node_id} - {str(e)}")
        return ""

def extract_text_with_newlines(node):
    """Извлекает текст с сохранением переносов строк"""
    text = ""
    
    # Если это текстовый узел
    if node.get("type") == "TEXT" and "characters" in node:
        text += node["characters"] + "\n"
    
    # Обработка дочерних элементов
    if "children" in node:
        for child in node["children"]:
            text += extract_text_with_newlines(child)
    
    return text

def get_last_text(frame_id):
    filepath = f"{HISTORY_DIR}/{frame_id}.txt"
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def save_last_text(frame_id, text):
    filepath = f"{HISTORY_DIR}/{frame_id}.txt"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

def find_added_lines(old, new):
    if not old:
        return new if new else ""
    
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    added_lines = []
    
    for i in range(len(new_lines)):
        if i >= len(old_lines) or new_lines[i] != old_lines[i]:
            added_lines.append(new_lines[i])
    
    return "\n".join(added_lines) if added_lines else ""

def format_message(title, changes):
    if not changes.strip():
        return ""
    
    message = f"<b>🔄 Обновление в {title}</b>\n\n"
    lines = changes.splitlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if any(month in line.lower() for month in ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]):
            message += f"<b>{line}</b>\n\n"
        else:
            message += f"{line}\n"
    
    return message.strip()

def send_to_telegram(message):
    if not message.strip():
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code != 200:
            print(f"[ERROR] Ошибка отправки: {response.text}")
    except Exception as e:
        print(f"[ERROR] Сетевая ошибка: {str(e)}")

def process_frame(config):
    frame_id = f"{config['file_id']}_{config['node_id']}"
    print(f"[INFO] Проверка фрейма {config['title']}")
    
    current_text = get_frame_text(config["file_id"], config["node_id"])
    if not current_text:
        return
    
    last_text = get_last_text(frame_id)
    changes = find_added_lines(last_text, current_text)
    
    if changes:
        message = format_message(config["title"], changes)
        if message:
            send_to_telegram(message)
            print(f"[INFO] Отправлены изменения для {config['title']}")
    
    save_last_text(frame_id, current_text)

def main():
    print(f"=== Запуск проверки {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    for config in FRAME_CONFIGS:
        try:
            process_frame(config)
        except Exception as e:
            print(f"[ERROR] Ошибка обработки {config['title']}: {str(e)}")
    
    print("=== Проверка завершена ===")

if __name__ == "__main__":
    main()