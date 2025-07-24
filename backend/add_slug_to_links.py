#!/usr/bin/env python3
"""
Скрипт для добавления колонки slug в таблицу PropertyYandexLink
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def add_slug_to_links():
    """Добавляет колонку slug в таблицу PropertyYandexLink"""
    with app.app_context():
        try:
            # Добавляем колонку slug
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE property_yandex_link ADD COLUMN slug VARCHAR(255)"))
                conn.commit()
            print("Колонка slug успешно добавлена в таблицу PropertyYandexLink")
        except Exception as e:
            print(f"Ошибка при добавлении колонки: {e}")
            # Проверяем, существует ли уже колонка
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(db.text("PRAGMA table_info(property_yandex_link)"))
                    columns = [row[1] for row in result]
                    if 'slug' in columns:
                        print("Колонка slug уже существует в таблице PropertyYandexLink")
                    else:
                        print("Не удалось добавить колонку slug")
            except Exception as e2:
                print(f"Ошибка при проверке колонок: {e2}")

if __name__ == "__main__":
    add_slug_to_links() 