#!/usr/bin/env python3
"""
Скрипт для обновления slug в таблице ЖК
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, YandexNewBuilding, generate_slug

def update_complex_slugs():
    """Обновляет slug для всех ЖК"""
    with app.app_context():
        # Получаем все ЖК без slug
        complexes = YandexNewBuilding.query.filter(
            (YandexNewBuilding.slug.is_(None)) | (YandexNewBuilding.slug == '')
        ).all()
        
        print(f"Найдено {len(complexes)} ЖК без slug")
        
        updated_count = 0
        for complex in complexes:
            if complex.complex_name:
                # Генерируем slug
                slug = generate_slug(complex.complex_name)
                
                # Проверяем уникальность
                counter = 1
                original_slug = slug
                while YandexNewBuilding.query.filter_by(slug=slug).first():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
                
                # Обновляем slug
                complex.slug = slug
                updated_count += 1
                print(f"Обновлен slug для '{complex.complex_name}' -> '{slug}'")
        
        # Сохраняем изменения
        db.session.commit()
        print(f"Обновлено {updated_count} ЖК")

if __name__ == "__main__":
    update_complex_slugs() 