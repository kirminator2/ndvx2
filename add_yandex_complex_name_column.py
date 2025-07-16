#!/usr/bin/env python3
"""
Скрипт для добавления полей в таблицу property_yandex_link
"""

import sqlite3
import os

def add_yandex_complex_name_column():
    """Добавляет недостающие поля в таблицу property_yandex_link"""
    
    # Путь к базе данных
    db_path = 'instance/real_estate.db'
    
    if not os.path.exists(db_path):
        print(f"База данных не найдена: {db_path}")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли уже поле
        cursor.execute("PRAGMA table_info(property_yandex_link)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Добавляем недостающие поля
        if 'property_id' not in columns:
            cursor.execute("ALTER TABLE property_yandex_link ADD COLUMN property_id INTEGER")
            print("Поле property_id добавлено в таблицу property_yandex_link")
        
        if 'yandex_complex_name' not in columns:
            cursor.execute("ALTER TABLE property_yandex_link ADD COLUMN yandex_complex_name VARCHAR(255)")
            print("Поле yandex_complex_name добавлено в таблицу property_yandex_link")
        
        # Сохраняем изменения
        conn.commit()
        conn.close()
        
        print("Миграция завершена успешно!")
        return True
        
    except Exception as e:
        print(f"Ошибка при выполнении миграции: {e}")
        return False

if __name__ == "__main__":
    add_yandex_complex_name_column() 