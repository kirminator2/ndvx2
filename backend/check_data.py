import sqlite3
import os

# Путь к базе данных
db_path = os.path.join('instance', 'real_estate.db')

print(f"Проверяем базу данных: {db_path}")
print(f"Файл существует: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Таблицы в базе данных: {[table[0] for table in tables]}")
    
    # Проверяем количество записей в основных таблицах
    for table in ['property', 'address', 'yandex_newbuildings']:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Записей в таблице {table}: {count}")
        except Exception as e:
            print(f"Ошибка при проверке таблицы {table}: {e}")
    
    # Проверяем несколько записей из property
    try:
        cursor.execute("SELECT id, title, address FROM property LIMIT 5")
        properties = cursor.fetchall()
        print(f"\nПервые 5 записей из property:")
        for prop in properties:
            print(f"  ID: {prop[0]}, Title: {prop[1]}, Address: {prop[2]}")
    except Exception as e:
        print(f"Ошибка при получении данных из property: {e}")
    
    conn.close()
else:
    print("Файл базы данных не найден!") 