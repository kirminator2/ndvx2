#!/usr/bin/env python3
"""
Скрипт для добавления полей ЖК в таблицы Address и Property
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Property, ResidentialComplex, Address, YandexNewBuilding, TrendBuilding
from sqlalchemy import text

def add_complex_fields_to_address():
    """Добавляет поля ЖК в таблицу Address"""
    
    with app.app_context():
        try:
            # Проверяем существующие поля
            existing_columns = db.session.execute(text("PRAGMA table_info(address)")).fetchall()
            existing_column_names = [col[1] for col in existing_columns]
            
            print(f"Существующие поля в Address: {existing_column_names}")
            
            # Добавляем поля только если их нет
            if 'yandex_complex_id' not in existing_column_names:
                db.session.execute(text("""
                    ALTER TABLE address 
                    ADD COLUMN yandex_complex_id INTEGER 
                    REFERENCES yandex_new_building(id)
                """))
                print("✅ Добавлено поле yandex_complex_id")
            else:
                print("ℹ️  Поле yandex_complex_id уже существует")
            
            if 'residential_complex_id' not in existing_column_names:
                db.session.execute(text("""
                    ALTER TABLE address 
                    ADD COLUMN residential_complex_id INTEGER 
                    REFERENCES residential_complex(id)
                """))
                print("✅ Добавлено поле residential_complex_id")
            else:
                print("ℹ️  Поле residential_complex_id уже существует")
            
            if 'trend_building_id' not in existing_column_names:
                db.session.execute(text("""
                    ALTER TABLE address 
                    ADD COLUMN trend_building_id INTEGER 
                    REFERENCES trend_building(id)
                """))
                print("✅ Добавлено поле trend_building_id")
            else:
                print("ℹ️  Поле trend_building_id уже существует")
            
            # Создаем индексы
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_address_yandex_complex_id 
                ON address(yandex_complex_id)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_address_residential_complex_id 
                ON address(residential_complex_id)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_address_trend_building_id 
                ON address(trend_building_id)
            """))
            
            print("✅ Индексы созданы для полей ЖК в Address")
            
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении полей в Address: {e}")
            db.session.rollback()
            return False

def add_complex_fields_to_property():
    """Добавляет поля ЖК в таблицу Property"""
    
    with app.app_context():
        try:
            # Проверяем существующие поля
            existing_columns = db.session.execute(text("PRAGMA table_info(property)")).fetchall()
            existing_column_names = [col[1] for col in existing_columns]
            
            print(f"Существующие поля в Property: {existing_column_names}")
            
            # Добавляем поля только если их нет
            if 'yandex_complex_id' not in existing_column_names:
                db.session.execute(text("""
                    ALTER TABLE property 
                    ADD COLUMN yandex_complex_id INTEGER 
                    REFERENCES yandex_new_building(id)
                """))
                print("✅ Добавлено поле yandex_complex_id")
            else:
                print("ℹ️  Поле yandex_complex_id уже существует")
            
            if 'residential_complex_id' not in existing_column_names:
                db.session.execute(text("""
                    ALTER TABLE property 
                    ADD COLUMN residential_complex_id INTEGER 
                    REFERENCES residential_complex(id)
                """))
                print("✅ Добавлено поле residential_complex_id")
            else:
                print("ℹ️  Поле residential_complex_id уже существует")
            
            if 'trend_building_id' not in existing_column_names:
                db.session.execute(text("""
                    ALTER TABLE property 
                    ADD COLUMN trend_building_id INTEGER 
                    REFERENCES trend_building(id)
                """))
                print("✅ Добавлено поле trend_building_id")
            else:
                print("ℹ️  Поле trend_building_id уже существует")
            
            # Создаем индексы
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_property_yandex_complex_id 
                ON property(yandex_complex_id)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_property_residential_complex_id 
                ON property(residential_complex_id)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_property_trend_building_id 
                ON property(trend_building_id)
            """))
            
            print("✅ Индексы созданы для полей ЖК в Property")
            
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении полей в Property: {e}")
            db.session.rollback()
            return False

def fill_address_complex_links():
    """Заполняет поля ЖК в таблице Address"""
    
    with app.app_context():
        try:
            # Заполняем yandex_complex_id
            db.session.execute(text("""
                UPDATE address 
                SET yandex_complex_id = (
                    SELECT id FROM yandex_newbuildings 
                    WHERE yandex_newbuildings.address_id = address.id
                    LIMIT 1
                )
                WHERE EXISTS (
                    SELECT 1 FROM yandex_newbuildings 
                    WHERE yandex_newbuildings.address_id = address.id
                )
            """))
            
            # Заполняем residential_complex_id
            db.session.execute(text("""
                UPDATE address 
                SET residential_complex_id = (
                    SELECT id FROM residential_complex 
                    WHERE residential_complex.address_id = address.id
                    LIMIT 1
                )
                WHERE EXISTS (
                    SELECT 1 FROM residential_complex 
                    WHERE residential_complex.address_id = address.id
                )
            """))
            
            # Заполняем trend_building_id
            db.session.execute(text("""
                UPDATE address 
                SET trend_building_id = (
                    SELECT id FROM trend_buildings 
                    WHERE trend_buildings.address_id = address.id
                    LIMIT 1
                )
                WHERE EXISTS (
                    SELECT 1 FROM trend_buildings 
                    WHERE trend_buildings.address_id = address.id
                )
            """))
            
            db.session.commit()
            
            # Статистика
            yandex_count = db.session.execute(text("SELECT COUNT(*) FROM address WHERE yandex_complex_id IS NOT NULL")).scalar()
            residential_count = db.session.execute(text("SELECT COUNT(*) FROM address WHERE residential_complex_id IS NOT NULL")).scalar()
            trend_count = db.session.execute(text("SELECT COUNT(*) FROM address WHERE trend_building_id IS NOT NULL")).scalar()
            
            print(f"✅ Заполнены поля ЖК в Address:")
            print(f"   - Yandex: {yandex_count}")
            print(f"   - Residential: {residential_count}")
            print(f"   - Trend: {trend_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при заполнении полей ЖК в Address: {e}")
            db.session.rollback()
            return False

def fill_property_complex_links():
    """Заполняет поля ЖК в таблице Property через Address"""
    
    with app.app_context():
        try:
            # Заполняем поля ЖК в Property через Address
            db.session.execute(text("""
                UPDATE property 
                SET yandex_complex_id = (
                    SELECT yandex_complex_id FROM address 
                    WHERE address.id = property.address_id
                )
                WHERE address_id IS NOT NULL
            """))
            
            db.session.execute(text("""
                UPDATE property 
                SET residential_complex_id = (
                    SELECT residential_complex_id FROM address 
                    WHERE address.id = property.address_id
                )
                WHERE address_id IS NOT NULL
            """))
            
            db.session.execute(text("""
                UPDATE property 
                SET trend_building_id = (
                    SELECT trend_building_id FROM address 
                    WHERE address.id = property.address_id
                )
                WHERE address_id IS NOT NULL
            """))
            
            db.session.commit()
            
            # Статистика
            yandex_count = db.session.execute(text("SELECT COUNT(*) FROM property WHERE yandex_complex_id IS NOT NULL")).scalar()
            residential_count = db.session.execute(text("SELECT COUNT(*) FROM property WHERE residential_complex_id IS NOT NULL")).scalar()
            trend_count = db.session.execute(text("SELECT COUNT(*) FROM property WHERE trend_building_id IS NOT NULL")).scalar()
            
            print(f"✅ Заполнены поля ЖК в Property:")
            print(f"   - Yandex: {yandex_count}")
            print(f"   - Residential: {residential_count}")
            print(f"   - Trend: {trend_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при заполнении полей ЖК в Property: {e}")
            db.session.rollback()
            return False

def update_models():
    """Обновляет модели в app.py"""
    
    address_model_code = '''
# Добавить в класс Address в app.py:
yandex_complex_id = db.Column(db.Integer, db.ForeignKey('yandex_new_building.id'))
residential_complex_id = db.Column(db.Integer, db.ForeignKey('residential_complex.id'))
trend_building_id = db.Column(db.Integer, db.ForeignKey('trend_building.id'))

# Отношения
yandex_complex = db.relationship('YandexNewBuilding', foreign_keys=[yandex_complex_id])
residential_complex = db.relationship('ResidentialComplex', foreign_keys=[residential_complex_id])
trend_building = db.relationship('TrendBuilding', foreign_keys=[trend_building_id])
'''
    
    property_model_code = '''
# Добавить в класс Property в app.py:
yandex_complex_id = db.Column(db.Integer, db.ForeignKey('yandex_new_building.id'))
residential_complex_id = db.Column(db.Integer, db.ForeignKey('residential_complex.id'))
trend_building_id = db.Column(db.Integer, db.ForeignKey('trend_building.id'))

# Отношения
yandex_complex = db.relationship('YandexNewBuilding', foreign_keys=[yandex_complex_id])
residential_complex = db.relationship('ResidentialComplex', foreign_keys=[residential_complex_id])
trend_building = db.relationship('TrendBuilding', foreign_keys=[trend_building_id])
'''
    
    print("📝 Обновите модели в app.py:")
    print("\nДля класса Address:")
    print(address_model_code)
    print("\nДля класса Property:")
    print(property_model_code)

def main():
    print("🏗️  Добавление полей ЖК в таблицы Address и Property")
    print("=" * 60)
    
    # Шаг 1: Добавляем поля в Address
    print("\n1️⃣ Добавление полей в таблицу Address...")
    if add_complex_fields_to_address():
        print("✅ Поля успешно добавлены в Address")
    else:
        print("❌ Не удалось добавить поля в Address")
        return
    
    # Шаг 2: Добавляем поля в Property
    print("\n2️⃣ Добавление полей в таблицу Property...")
    if add_complex_fields_to_property():
        print("✅ Поля успешно добавлены в Property")
    else:
        print("❌ Не удалось добавить поля в Property")
        return
    
    # Шаг 3: Заполняем поля в Address
    print("\n3️⃣ Заполнение полей ЖК в Address...")
    if fill_address_complex_links():
        print("✅ Поля успешно заполнены в Address")
    else:
        print("❌ Не удалось заполнить поля в Address")
        return
    
    # Шаг 4: Заполняем поля в Property
    print("\n4️⃣ Заполнение полей ЖК в Property...")
    if fill_property_complex_links():
        print("✅ Поля успешно заполнены в Property")
    else:
        print("❌ Не удалось заполнить поля в Property")
        return
    
    # Шаг 5: Инструкции по обновлению моделей
    print("\n📝 Следующие шаги:")
    update_models()
    
    print("\n🎉 Миграция завершена успешно!")
    print("\nТеперь вы можете:")
    print("1. Использовать поля ЖК для прямых связей")
    print("2. Быстро получать информацию о ЖК из Property")
    print("3. Фильтровать квартиры по типу ЖК")

if __name__ == "__main__":
    main() 