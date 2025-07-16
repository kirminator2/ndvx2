from app import app, db, Property, PropertyYandexLink, ResidentialComplex

app.app_context().push()

links = PropertyYandexLink.query.all()
with_complex_id = 0
with_complex_obj = 0
for link in links:
    prop = Property.query.get(link.property_id)
    if not prop:
        continue
    if prop.complex_id:
        with_complex_id += 1
        complex_obj = ResidentialComplex.query.get(prop.complex_id)
        if complex_obj:
            with_complex_obj += 1
print(f"PropertyYandexLink всего: {len(links)}")
print(f"С complex_id у Property: {with_complex_id}")
print(f"Существующий ResidentialComplex: {with_complex_obj}") 