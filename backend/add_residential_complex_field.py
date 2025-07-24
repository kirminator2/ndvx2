#!/usr/bin/env python3
"""
Скрипт для добавления поля residential_complex_id в таблицу Property
и создания связей между квартирами и жилыми комплексами
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Property, ResidentialComplex, Address
from sqlalchemy import text

def add_residential_complex_field():
    """Добавляет поле residential_complex_id в таблицу Property"""
    
    with app.app_context():
        try:
            # Добавляем новое поле в таблицу Property
            db.session.execute(text("""
                ALTER TABLE property 
                ADD COLUMN residential_complex_id INTEGER 
                REFERENCES residential_complex(id)
            """))
            
            print("✅ Поле residential_complex_id добавлено в таблицу Property")
            
            # Создаем индекс для быстрого поиска
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_property_residential_complex_id 
                ON property(residential_complex_id)
            """))
            
            print("✅ Индекс создан для поля residential_complex_id")
            
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении поля: {e}")
            db.session.rollback()
            return False

def create_complex_property_links():
    """Создает связи между квартирами и ЖК на основе адресов"""
    
    with app.app_context():
        try:
            # Получаем все ЖК с адресами
            complexes = ResidentialComplex.query.filter(
                ResidentialComplex.address_id.isnot(None)
            ).all()
            
            print(f"Найдено {len(complexes)} ЖК с адресами")
            
            linked_count = 0
            
            for complex_obj in complexes:
                # Находим все квартиры с тем же адресом
                properties = Property.query.filter(
                    Property.address_id == complex_obj.address_id
                ).all()
                
                if properties:
                    # Обновляем поле residential_complex_id для всех квартир
                    for prop in properties:
                        prop.residential_complex_id = complex_obj.id
                    
                    linked_count += len(properties)
                    print(f"ЖК '{complex_obj.name}': связано {len(properties)} квартир")
            
            db.session.commit()
            print(f"✅ Всего связано {linked_count} квартир с ЖК")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при создании связей: {e}")
            db.session.rollback()
            return False

def update_property_model():
    """Обновляет модель Property для включения нового поля"""
    
    # Добавляем в модель Property новое поле
    property_model_code = '''
    # Добавить в класс Property в app.py:
    residential_complex_id = db.Column(db.Integer, db.ForeignKey('residential_complex.id'))
    residential_complex = db.relationship('ResidentialComplex', backref='properties')
    '''
    
    print("📝 Обновите модель Property в app.py:")
    print(property_model_code)

def main():
    print("🏗️  Добавление поля residential_complex_id в таблицу Property")
    print("=" * 60)
    
    # Шаг 1: Добавляем поле
    if add_residential_complex_field():
        print("\n✅ Поле успешно добавлено")
    else:
        print("\n❌ Не удалось добавить поле")
        return
    
    # Шаг 2: Создаем связи
    print("\n🔗 Создание связей между квартирами и ЖК...")
    if create_complex_property_links():
        print("\n✅ Связи успешно созданы")
    else:
        print("\n❌ Не удалось создать связи")
        return
    
    # Шаг 3: Инструкции по обновлению модели
    print("\n📝 Следующие шаги:")
    update_property_model()
    
    print("\n🎉 Миграция завершена успешно!")
    print("\nТеперь вы можете:")
    print("1. Использовать поле residential_complex_id для прямых связей")
    print("2. Сохранить PropertyYandexLink для Яндекс-данных")
    print("3. Создавать красивые URL для ЖК")

if __name__ == "__main__":
    main()