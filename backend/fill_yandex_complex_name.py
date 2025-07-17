from app import app, db, Property, PropertyYandexLink, ResidentialComplex

app.app_context().push()

links = PropertyYandexLink.query.all()
updated = 0
skipped = 0
for link in links:
    # Найти объект
    prop = Property.query.get(link.property_id)
    if not prop:
        skipped += 1
        continue
    # Если уже заполнено, пропустить
    if link.yandex_complex_name:
        skipped += 1
        continue
    # Если есть complex_id, ищем ЖК
    if prop.complex_id:
        complex_obj = ResidentialComplex.query.get(prop.complex_id)
        if complex_obj and complex_obj.name:
            link.yandex_complex_name = complex_obj.name
            updated += 1
        else:
            skipped += 1
    else:
        skipped += 1

db.session.commit()
print(f"Обновлено связей: {updated}")
print(f"Пропущено: {skipped}") 