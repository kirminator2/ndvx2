from app import app, db, Property, PropertyYandexLink

app.app_context().push()

# Проверяем общее количество объектов
total_properties = Property.query.count()
print(f"Всего объектов: {total_properties}")

# Проверяем количество объектов со связями с ЖК
properties_with_links = Property.query.join(PropertyYandexLink).count()
print(f"Объектов со связями с ЖК: {properties_with_links}")

# Проверяем количество объектов с заполненным названием ЖК
properties_with_complex_name = db.session.query(Property).join(PropertyYandexLink).filter(
    PropertyYandexLink.yandex_complex_name.isnot(None),
    PropertyYandexLink.yandex_complex_name != ''
).count()
print(f"Объектов с названием ЖК: {properties_with_complex_name}")

# Показываем несколько примеров
print("\nПримеры объектов со связями:")
links = db.session.query(Property, PropertyYandexLink).join(PropertyYandexLink).limit(5).all()
for prop, link in links:
    print(f"ID: {prop.id}, Title: {prop.title}, ЖК: {link.yandex_complex_name}")

# Проверяем уникальные названия ЖК
complex_names = db.session.query(PropertyYandexLink.yandex_complex_name).filter(
    PropertyYandexLink.yandex_complex_name.isnot(None),
    PropertyYandexLink.yandex_complex_name != ''
).distinct().limit(10).all()

print(f"\nУникальные названия ЖК (первые 10):")
for (name,) in complex_names:
    print(f"- {name}") 