from app import app, db
from sqlalchemy import text

def add_complex_photos_table():
    """Добавляет таблицу complex_photos к существующей базе данных"""
    with app.app_context():
        try:
            # Создаем таблицу complex_photos
            db.session.execute(text("""
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
            """))
            db.session.commit()
            print("✅ Таблица complex_photos успешно создана")
            
            # Проверяем, что таблица создана
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='complex_photos'"))
            if result.fetchone():
                print("✅ Таблица complex_photos существует в базе данных")
            else:
                print("❌ Ошибка: таблица complex_photos не была создана")
                
        except Exception as e:
            print(f"❌ Ошибка при создании таблицы complex_photos: {e}")

if __name__ == '__main__':
    add_complex_photos_table() 