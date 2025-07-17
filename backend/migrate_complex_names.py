from app import app, db, PropertyYandexLink
from sqlalchemy import text

with app.app_context():
    print("🔍 Проверяем структуру таблиц...")
    
    # Проверяем существование старой таблицы
    result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='property_yandex_link_old'"))
    old_table_exists = result.fetchone() is not None
    
    if not old_table_exists:
        print("❌ Таблица property_yandex_link_old не найдена")
        exit(1)
    
    print("✅ Старая таблица найдена")
    
    # Получаем данные из старой таблицы
    old_links = db.session.execute(text("""
        SELECT property_id, yandex_complex_name 
        FROM property_yandex_link_old 
        WHERE yandex_complex_name IS NOT NULL 
        AND yandex_complex_name != ''
    """)).fetchall()
    
    print(f"📊 Найдено {len(old_links)} записей с названиями в старой таблице")
    
    if not old_links:
        print("❌ В старой таблице нет записей с названиями")
        exit(1)
    
    # Обновляем новую таблицу
    updated_count = 0
    for old_link in old_links:
        property_id = old_link[0]
        complex_name = old_link[1]
        
        # Находим запись в новой таблице
        new_link = PropertyYandexLink.query.filter_by(property_id=property_id).first()
        
        if new_link:
            if not new_link.yandex_complex_name or new_link.yandex_complex_name == '':
                new_link.yandex_complex_name = complex_name
                updated_count += 1
                print(f"✅ Обновлен объект {property_id}: '{complex_name}'")
        else:
            print(f"⚠️  Объект {property_id} не найден в новой таблице")
    
    # Сохраняем изменения
    db.session.commit()
    
    print(f"🎉 Обновлено {updated_count} записей")
    
    # Проверяем результат
    total_with_names = PropertyYandexLink.query.filter(
        PropertyYandexLink.yandex_complex_name.isnot(None),
        PropertyYandexLink.yandex_complex_name != ''
    ).count()
    
    print(f"📈 Теперь в новой таблице {total_with_names} записей с названиями") 