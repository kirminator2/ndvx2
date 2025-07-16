from app import app, db, PropertyYandexLink, Property

with app.app_context():
    total_links = PropertyYandexLink.query.count()
    print(f"Всего связей с Яндекс ЖК: {total_links}")
    
    # Ищем связи с заполненными названиями
    links_with_names = PropertyYandexLink.query.filter(
        PropertyYandexLink.yandex_complex_name.isnot(None),
        PropertyYandexLink.yandex_complex_name != ''
    ).count()
    print(f"Связей с заполненными названиями: {links_with_names}")
    
    if links_with_names > 0:
        # Показываем первые 5 связей с названиями
        links = PropertyYandexLink.query.filter(
            PropertyYandexLink.yandex_complex_name.isnot(None),
            PropertyYandexLink.yandex_complex_name != ''
        ).limit(5).all()
        for link in links:
            print(f"Связь {link.id}: property_id={link.property_id}, complex_name='{link.yandex_complex_name}'")
    else:
        print("Связей с заполненными названиями не найдено")
        
    # Проверяем общее количество объектов
    total_properties = Property.query.count()
    print(f"Всего объектов недвижимости: {total_properties}") 