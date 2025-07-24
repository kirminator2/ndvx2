#!/usr/bin/env python3
"""
Скрипт для обновления slug в таблице PropertyYandexLink
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, PropertyYandexLink, generate_slug

def update_link_slugs():
    """Обновляет slug для всех связей в PropertyYandexLink"""
    with app.app_context():
        # Получаем все связи без slug
        links = PropertyYandexLink.query.filter(
            (PropertyYandexLink.slug.is_(None)) | (PropertyYandexLink.slug == '')
        ).all()
        
        print(f"Найдено {len(links)} связей без slug")
        
        # Группируем по complex_name для создания уникальных slug
        complex_groups = {}
        for link in links:
            if link.yandex_complex_name:
                if link.yandex_complex_name not in complex_groups:
                    complex_groups[link.yandex_complex_name] = []
                complex_groups[link.yandex_complex_name].append(link)
        
        updated_count = 0
        for complex_name, group_links in complex_groups.items():
            # Генерируем базовый slug для комплекса
            base_slug = generate_slug(complex_name)
            
            # Проверяем уникальность slug в таблице связей
            counter = 1
            original_slug = base_slug
            while PropertyYandexLink.query.filter_by(slug=base_slug).first():
                base_slug = f"{original_slug}-{counter}"
                counter += 1
            
            # Обновляем все связи для этого комплекса
            for link in group_links:
                link.slug = base_slug
                updated_count += 1
                print(f"Обновлен slug для связи {link.id} (комплекс: '{complex_name}') -> '{base_slug}'")
        
        # Сохраняем изменения
        db.session.commit()
        print(f"Обновлено {updated_count} связей")

if __name__ == "__main__":
    update_link_slugs() 