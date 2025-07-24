#!/usr/bin/env python3
"""
Скрипт для добавления колонки slug в таблицу address
"""

import sqlite3
import os

def add_slug_column():
    """Добавляет колонку slug в таблицу address"""
    
    # Путь к базе данных
    db_path = "instance/real_estate.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли уже колонка slug
        cursor.execute("PRAGMA table_info(address)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'slug' in columns:
            print("✅ Колонка slug уже существует в таблице address")
            return True
        
        # Добавляем колонку slug (без UNIQUE, добавим индекс позже)
        cursor.execute("""
            ALTER TABLE address 
            ADD COLUMN slug VARCHAR(255)
        """)
        
        # Создаем индекс для быстрого поиска
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_address_slug 
            ON address(slug)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Колонка slug успешно добавлена в таблицу address")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении колонки: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Добавление колонки slug в таблицу address...")
    success = add_slug_column()
    
    if success:
        print("✅ Миграция завершена успешно!")
    else:
        print("❌ Миграция завершена с ошибками!") 