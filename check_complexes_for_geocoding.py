from app import app, db, ResidentialComplex

app.app_context().push()

# Найти ЖК, которые имеют координаты, но не имеют адреса
complexes = ResidentialComplex.query.filter(
    ResidentialComplex.latitude.isnot(None),
    ResidentialComplex.longitude.isnot(None),
    ResidentialComplex.address_id.is_(None)
).all()

print(f"ЖК для геокодирования: {len(complexes)}")

if complexes:
    print("\nПервые 5 ЖК для геокодирования:")
    for i, c in enumerate(complexes[:5], 1):
        print(f"{i}. ID: {c.id}, Name: {c.name}, Lat: {c.latitude}, Lon: {c.longitude}")
else:
    print("Нет ЖК для геокодирования - все уже имеют адреса")

# Также проверим общее количество ЖК
total_complexes = ResidentialComplex.query.count()
complexes_with_coords = ResidentialComplex.query.filter(
    ResidentialComplex.latitude.isnot(None),
    ResidentialComplex.longitude.isnot(None)
).count()
complexes_with_address = ResidentialComplex.query.filter(
    ResidentialComplex.address_id.isnot(None)
).count()

print(f"\nОбщая статистика:")
print(f"Всего ЖК: {total_complexes}")
print(f"ЖК с координатами: {complexes_with_coords}")
print(f"ЖК с адресами: {complexes_with_address}") 