import os
import re
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

def sanitize_filename(filename):
    """Заменяет недопустимые символы в именах файлов"""
    return re.sub(r'[:]', '_', filename)

def get_frame_text(file_id, node_id):
    """Получает текст из Figma с сохранением структуры"""
    url = f"https://api.figma.com/v1/files/{file_id}/nodes?ids={node_id}"
    headers = {"X-Figma-Token": FIGMA_TOKEN}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        node = data["nodes"][node_id]["document"]
        return extract_text_preserve_structure(node)
    except Exception as e:
        print(f"[ERROR] Ошибка получения текста для {file_id}:{node_id} - {str(e)}")
        return ""

def extract_text_preserve_structure(node):
    """Извлекает текст, сохраняя оригинальную структуру строк"""
    text = ""
    
    if node.get("type") == "TEXT" and "characters" in node:
        text += node["characters"] + "\n"
    
    if "children" in node:
        for child in node["children"]:
            text += extract_text_preserve_structure(child)
    
    return text

def get_last_text(frame_id):
    safe_filename = sanitize_filename(frame_id)
    filepath = f"{HISTORY_DIR}/{safe_filename}.txt"
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def save_last_text(frame_id, text):
    safe_filename = sanitize_filename(frame_id)
    filepath = f"{HISTORY_DIR}/{safe_filename}.txt"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

def find_new_entries(old_text, new_text):
    """Находит новые записи, сохраняя группировку по датам"""
    if not old_text:
        return new_text
    
    old_entries = split_into_entries(old_text)
    new_entries = split_into_entries(new_text)
    
    added_entries = []
    for date, entries in new_entries.items():
        if date not in old_entries:
            added_entries.append((date, entries))
        else:
            new_items = [e for e in entries if e not in old_entries[date]]
            if new_items:
                added_entries.append((date, new_items))
    
    return added_entries

def split_into_entries(text):
    """Разбивает текст на записи, сгруппированные по датам"""
    entries = {}
    current_date = None
    current_items = []
    
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
            
        # Проверяем, является ли строка датой
        if any(month in line.lower() for month in ["янв", "фев", "мар", "апр", "май", "июн", 
                                                "июл", "авг", "сен", "окт", "ноя", "дек"]):
            if current_date:
                entries[current_date] = current_items
            current_date = line
            current_items = []
        else:
            current_items.append(line)
    
    if current_date:
        entries[current_date] = current_items
    
    return entries

def format_entries(title, entries):
    """Форматирует записи для Telegram"""
    if not entries:
        return ""
    
    message = f"<b>🔄 Обновление в {title}</b>\n\n"
    
    for date, items in entries:
        message += f"<b>{date}</b>\n"
        for item in items:
            message += f"{item}\n"
        message += "\n"
    
    return message.strip()

def send_telegram_message(message):
    """Отправляет сообщение в Telegram"""
    if not message or not message.strip():
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            return True
        print(f"[ERROR] Telegram API: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"[ERROR] Ошибка отправки: {str(e)}")
    
    return False

def process_frame(config):
    frame_id = f"{config['file_id']}_{config['node_id']}"
    print(f"\n[INFO] Проверка фрейма: {config['title']}")
    
    # Получаем текущий текст
    current_text = get_frame_text(config["file_id"], config["node_id"])
    if not current_text:
        print("[WARNING] Не удалось получить текст из Figma")
        return
    
    print("[DEBUG] Текущий текст из Figma:")
    print(current_text)
    
    # Получаем предыдущую версию
    last_text = get_last_text(frame_id)
    
    # Находим новые записи
    new_entries = find_new_entries(last_text, current_text)
    
    if new_entries:
        # Форматируем и отправляем сообщение
        message = format_entries(config["title"], new_entries)
        print("[DEBUG] Форматированное сообщение:")
        print(message)
        
        if send_telegram_message(message):
            print("[SUCCESS] Сообщение успешно отправлено")
        else:
            print("[ERROR] Не удалось отправить сообщение")
        
        # Сохраняем новую версию
        save_last_text(frame_id, current_text)
    else:
        print("[INFO] Новых изменений не обнаружено")

def main():
    print(f"\n=== Запуск проверки {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    for config in FRAME_CONFIGS:
        try:
            process_frame(config)
        except Exception as e:
            print(f"[ERROR] Ошибка обработки {config['title']}: {str(e)}")
    
    print("\n=== Проверка завершена ===")

if __name__ == "__main__":
    main()