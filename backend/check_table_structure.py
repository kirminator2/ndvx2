#!/usr/bin/env python3
import sqlite3

def check_table_structure():
    conn = sqlite3.connect('instance/real_estate.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(property_yandex_link)")
    columns = cursor.fetchall()
    print("Структура таблицы property_yandex_link:")
    for column in columns:
        print(f"  - {column[1]} ({column[2]})")
    conn.close()

if __name__ == "__main__":
    check_table_structure() 