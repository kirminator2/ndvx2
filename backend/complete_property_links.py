#!/usr/bin/env python3
"""
Скрипт для завершения обновления связей Property с ЖК
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Property, Address

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
                if address and hasattr(address, 'residential_complex_id'):
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

def main():
    print("🏗️  Завершение обновления связей Property с ЖК")
    print("=" * 50)
    
    # Обновляем связи Property
    print("\n🔄 Обновление связей Property...")
    if update_property_complex_links():
        print("✅ Связи Property обновлены")
    else:
        print("❌ Не удалось обновить связи Property")
        return
    
    print("\n🎉 Обновление завершено успешно!")
    print("\nТеперь структура связей:")
    print("Property → Address → ResidentialComplex")
    print("Property → Address → YandexNewBuilding")
    print("Property → Address → TrendBuilding")

if __name__ == "__main__":
    main() 