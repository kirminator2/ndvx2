import os
import sqlite3
from app import app, db

def reset_database():
    with app.app_context():
        # Удаляем все таблицы
        db.drop_all()
        
        # Создаем все таблицы заново
        db.create_all()
        
        print("База данных сброшена и создана заново")
        
        # Создаем таблицу complex_photos если её нет
        try:
            db.engine.execute("""
                CREATE TABLE IF NOT EXISTS complex_photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    complex_id INTEGER NOT NULL,
                    photo_path VARCHAR(512) NOT NULL,
                    photo_url VARCHAR(512),
                    title VARCHAR(255),
                    is_main BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (complex_id) REFERENCES residential_complex (id)
                )
            """)
            print("Таблица complex_photos создана")
        except Exception as e:
            print(f"Ошибка при создании таблицы complex_photos: {e}")
        
        # Проверяем, что таблицы созданы
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Созданные таблицы: {tables}")
        
        # Проверяем структуру таблицы Property
        if 'property' in tables:
            columns = [col['name'] for col in inspector.get_columns('property')]
            print(f"Колонки таблицы Property: {columns}")
            
            # Проверяем наличие address_id
            if 'address_id' in columns:
                print("✅ Колонка address_id успешно добавлена")
            else:
                print("❌ Колонка address_id отсутствует")
        
        # Проверяем структуру таблицы Address
        if 'address' in tables:
            columns = [col['name'] for col in inspector.get_columns('address')]
            print(f"Колонки таблицы Address: {columns}")
            if 'fias_id' in columns:
                print("✅ Колонка fias_id успешно добавлена в Address")
            else:
                print("❌ Колонка fias_id отсутствует в Address")

if __name__ == '__main__':
    reset_database() 