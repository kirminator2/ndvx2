#!/usr/bin/env python3
"""
Добавляет поле trend_block_id в таблицу yandex_newbuildings
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app, db
from sqlalchemy import text

def add_trend_block_id():
    with app.app_context():
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('yandex_newbuildings')]
        if 'trend_block_id' not in columns:
            db.session.execute(text("ALTER TABLE yandex_newbuildings ADD COLUMN trend_block_id VARCHAR(64)"))
            db.session.commit()
            print("Поле trend_block_id успешно добавлено!")
        else:
            print("Поле trend_block_id уже существует.")

if __name__ == "__main__":
    add_trend_block_id() 