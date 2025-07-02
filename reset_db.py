import os
import sqlite3
from app import app, db

def reset_database():
    """Удаляет старую базу данных и создает новую с правильной схемой (включая fias_id в Address)"""
    
    # Удаляем файл базы данных если он существует
    db_path = 'real_estate.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Удален файл базы данных: {db_path}")
    
    # Создаем новую базу данных с правильной схемой
    with app.app_context():
        db.create_all()
        print("Создана новая база данных с обновленной схемой (fias_id в Address)")
        
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