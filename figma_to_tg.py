import os
import requests
import hashlib
import json

from config import FRAME_CONFIGS

# Загрузка переменных из окружения
FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHANNEL_ID")
THREAD_ID = os.getenv("TELEGRAM_THREAD_ID")

try:
    THREAD_ID = int(THREAD_ID)
except:
    THREAD_ID = None

HEADERS = {"X-Figma-Token": FIGMA_TOKEN}

HISTORY_DIR = "history"
os.makedirs(HISTORY_DIR, exist_ok=True)


def get_frame_text(file_id, node_id):
    url = f"https://api.figma.com/v1/files/{file_id}/nodes?ids={node_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"[FIGMA] Error {response.status_code}: {response.text}")
    
    node = response.json()["nodes"][node_id]["document"]
    return extract_text(node)


def extract_text(node):
    result = []

    def recurse(n):
        if n["type"] == "TEXT" and "characters" in n:
            text = n["characters"].strip()
            if text:
                result.append(text)
        for child in n.get("children", []):
            recurse(child)

    recurse(node)
    return result


def load_hash(frame_id):
    path = os.path.join(HISTORY_DIR, f"{frame_id}.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def save_hash(frame_id, text_list):
    full_text = "\n".join(text_list).strip()
    hash_val = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
    path = os.path.join(HISTORY_DIR, f"{frame_id}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(hash_val)
    return hash_val


def compute_hash(text_list):
    return hashlib.sha256("\n".join(text_list).strip().encode("utf-8")).hexdigest()


def get_diff(old_list, new_list):
    old_set = set(old_list)
    return [line for line in new_list if line not in old_set and line.strip()]


def send_telegram_message(message, thread_id=None):
    if not message.strip():
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    if thread_id is not None:
        data["message_thread_id"] = thread_id

    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            return True
        print(f"[TELEGRAM ERROR] {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[EXCEPTION] Telegram send failed: {e}")
    return False


def process_frame(frame_config):
    file_id = frame_config["file_id"]
    node_id = frame_config["node_id"]
    title = frame_config["title"]
    frame_key = f"{file_id}_{node_id}".replace(":", "_")

    print(f"📂 Обрабатываем фрейм: {title}")
    try:
        current_text = get_frame_text(file_id, node_id)
    except Exception as e:
        print(f"❌ Ошибка получения текста: {e}")
        return

    new_hash = compute_hash(current_text)
    old_hash = load_hash(frame_key)

    if new_hash == old_hash:
        print("✅ Без изменений.")
        return

    diff_lines = get_diff([], current_text) if not old_hash else get_diff(load_text_list(frame_key), current_text)

    if not diff_lines:
        print("⚠️ Хэш изменился, но новых строк не найдено.")
    else:
        message = f"<b>{title} — обновления</b>\n\n" + "\n".join(f"• {line}" for line in diff_lines)
        if send_telegram_message(message, THREAD_ID):
            print("📤 Изменения отправлены.")
        else:
            print("❌ Ошибка отправки в Telegram.")

    save_text_list(frame_key, current_text)
    save_hash(frame_key, current_text)


def load_text_list(frame_key):
    path = os.path.join(HISTORY_DIR, f"{frame_key}_text.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_text_list(frame_key, text_list):
    path = os.path.join(HISTORY_DIR, f"{frame_key}_text.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(text_list, f, ensure_ascii=False, indent=2)


def main():
    print("🚀 Запуск процесса...")

    for frame in FRAME_CONFIGS:
        process_frame(frame)

    print("✅ Готово.")


if __name__ == "__main__":
    main()
