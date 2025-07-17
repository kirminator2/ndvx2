#!/usr/bin/env python3
import sqlite3

def check_tables():
    conn = sqlite3.connect('instance/real_estate.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print("Существующие таблицы:")
    for table in tables:
        print(f"  - {table}")
    conn.close()

if __name__ == "__main__":
    check_tables() 