#!/usr/bin/env python3
"""
Скрипт для добавления связей ЖК в таблицу Address
и обновления связей Property с ЖК
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Property, ResidentialComplex, Address, YandexNewBuilding, TrendBuilding
from sqlalchemy import text

def add_complex_links_to_address():
    """Добавляет поля связей с ЖК в таблицу Address"""
    
    with app.app_context():
        try:
            # Добавляем поля в таблицу Address
            db.session.execute(text("""
                ALTER TABLE address 
                ADD COLUMN residential_complex_id INTEGER 
                REFERENCES residential_complex(id)
            """))
            
            db.session.execute(text("""
                ALTER TABLE address 
                ADD COLUMN yandex_complex_id INTEGER 
                REFERENCES yandex_newbuildings(id)
            """))
            
            db.session.execute(text("""
                ALTER TABLE address 
                ADD COLUMN trend_building_id VARCHAR 
                REFERENCES trend_buildings(id)
            """))
            
            print("✅ Поля связей с ЖК добавлены в таблицу Address")
            
            # Создаем индексы
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_address_residential_complex_id 
                ON address(residential_complex_id)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_address_yandex_complex_id 
                ON address(yandex_complex_id)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_address_trend_building_id 
                ON address(trend_building_id)
            """))
            
            print("✅ Индексы созданы")
            
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении полей: {e}")
            db.session.rollback()
            return False

def populate_complex_links():
    """Заполняет связи ЖК в таблице Address"""
    
    with app.app_context():
        try:
            # 1. Связываем ResidentialComplex с Address
            complexes = ResidentialComplex.query.filter(
                ResidentialComplex.address_id.isnot(None)
            ).all()
            
            for complex_obj in complexes:
                address = Address.query.get(complex_obj.address_id)
                if address:
                    address.residential_complex_id = complex_obj.id
                    print(f"ЖК '{complex_obj.name}' → Address {address.id}")
            
            # 2. Связываем YandexNewBuilding с Address
            yandex_buildings = YandexNewBuilding.query.filter(
                YandexNewBuilding.address_id.isnot(None)
            ).all()
            
            for building in yandex_buildings:
                address = Address.query.get(building.address_id)
                if address:
                    address.yandex_complex_id = building.id
                    print(f"Яндекс ЖК '{building.complex_name}' → Address {address.id}")
            
            # 3. Связываем TrendBuilding с Address
            trend_buildings = TrendBuilding.query.filter(
                TrendBuilding.address_id.isnot(None)
            ).all()
            
            for building in trend_buildings:
                address = Address.query.get(building.address_id)
                if address:
                    address.trend_building_id = building.id
                    print(f"Trend ЖК '{building.name}' → Address {address.id}")
            
            db.session.commit()
            print("✅ Связи ЖК заполнены в таблице Address")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при заполнении связей: {e}")
            db.session.rollback()
            return False

def update_property_complex_links():
    """Обновляет связи Property с ЖК через Address"""
    
    with app.app_context():
        try:
            # Получаем все квартиры с адресами
            properties = Property.query.filter(
                Property.address_id.isnot(None)
            ).all()
            
            updated_count = 0
            
            for prop in properties:
                address = Address.query.get(prop.address_id)
                if address:
                    # Обновляем связи через адрес
                    if address.residential_complex_id:
                        prop.residential_complex_id = address.residential_complex_id
                        updated_count += 1
                        print(f"Property {prop.id} → ЖК {address.residential_complex_id}")
            
            db.session.commit()
            print(f"✅ Обновлено {updated_count} квартир с ЖК")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении связей Property: {e}")
            db.session.rollback()
            return False

def update_address_model():
    """Обновляет модель Address для включения новых полей"""
    
    address_model_code = '''
    # Добавить в класс Address в app.py:
    residential_complex_id = db.Column(db.Integer, db.ForeignKey('residential_complex.id'))
    yandex_complex_id = db.Column(db.Integer, db.ForeignKey('yandex_newbuildings.id'))
    trend_building_id = db.Column(db.String, db.ForeignKey('trend_buildings.id'))
    
    # Добавить отношения:
    residential_complex = db.relationship('ResidentialComplex', backref='addresses')
    yandex_complex = db.relationship('YandexNewBuilding', backref='addresses')
    trend_building = db.relationship('TrendBuilding', backref='addresses')
    '''
    
    print("📝 Обновите модель Address в app.py:")
    print(address_model_code)

def main():
    print("🏗️  Обновление структуры связей ЖК")
    print("=" * 50)
    
    # Шаг 1: Добавляем поля в Address
    print("\n1️⃣ Добавление полей в таблицу Address...")
    if add_complex_links_to_address():
        print("✅ Поля добавлены")
    else:
        print("❌ Не удалось добавить поля")
        return
    
    # Шаг 2: Заполняем связи
    print("\n2️⃣ Заполнение связей ЖК...")
    if populate_complex_links():
        print("✅ Связи заполнены")
    else:
        print("❌ Не удалось заполнить связи")
        return
    
    # Шаг 3: Обновляем связи Property
    print("\n3️⃣ Обновление связей Property...")
    if update_property_complex_links():
        print("✅ Связи Property обновлены")
    else:
        print("❌ Не удалось обновить связи Property")
        return
    
    # Шаг 4: Инструкции по обновлению модели
    print("\n4️⃣ Следующие шаги:")
    update_address_model()
    
    print("\n🎉 Миграция завершена успешно!")
    print("\nТеперь структура связей:")
    print("Property → Address → ResidentialComplex")
    print("Property → Address → YandexNewBuilding")
    print("Property → Address → TrendBuilding")

if __name__ == "__main__":
    main() 