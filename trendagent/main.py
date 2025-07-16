import os
import requests

# Папка для сохранения файлов
SAVE_DIR = "krd"
os.makedirs(SAVE_DIR, exist_ok=True)

# Файл со списком ссылок
LIST_FILE = "list.txt"

# Функция для скачивания файла
def download_file(url, save_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Скачано: {save_path}")
    except requests.RequestException as e:
        print(f"Ошибка при скачивании {url}: {e}")

# Читаем список ссылок и загружаем файлы
with open(LIST_FILE, "r", encoding="utf-8") as file:
    for line in file:
        url = line.strip()
        if url:
            filename = os.path.join(SAVE_DIR, os.path.basename(url))
            download_file(url, filename)

print("Загрузка завершена.")
