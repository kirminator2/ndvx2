import functools
import signal
import threading

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
from datetime import datetime
import re
import requests
import time
import json
import json as pyjson
import csv
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy import or_
from g4f.client import Client

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///real_estate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Конфигурация DaData API
DADATA_API_KEY = "f669e45441f161c998910e5716089df35de51bcc"
DADATA_API_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/geolocate/address"

ANTIZNAK_KEY = "72UL79FJ32"

STOP_GEOCODING_TASKS = False


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fias_id = db.Column(db.String(36), unique=True, nullable=True)  # Новый уникальный идентификатор ФИАС
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    dadata_address = db.Column(db.String(500))
    dadata_full_address = db.Column(db.String(500))
    postal_code = db.Column(db.String(10))
    country = db.Column(db.String(100))
    region = db.Column(db.String(100))
    city = db.Column(db.String(100))
    street = db.Column(db.String(200))
    house = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.String(50))
    description = db.Column(db.Text)
    title = db.Column(db.String(500))
    content = db.Column(db.Text)
    note = db.Column(db.Text)
    plot_area = db.Column(db.Float)
    min_plot_area = db.Column(db.Float)
    total_area = db.Column(db.Float)
    min_area = db.Column(db.Float)
    living_area = db.Column(db.Float)
    kitchen_area = db.Column(db.Float)
    facade = db.Column(db.String(100))
    total_floors = db.Column(db.Integer)
    floor = db.Column(db.Integer)
    rooms_count = db.Column(db.Integer)
    isolated_rooms = db.Column(db.Integer)
    total_rooms = db.Column(db.Integer)
    price = db.Column(db.Float)
    min_price = db.Column(db.Float)
    address = db.Column(db.String(500))
    house = db.Column(db.String(50))
    building = db.Column(db.String(50))
    letter = db.Column(db.String(10))
    landmark = db.Column(db.String(200))
    construction_year = db.Column(db.Integer)
    delivery_quarter = db.Column(db.String(50))
    house_part = db.Column(db.String(100))
    house_readiness = db.Column(db.String(100))
    exclusive = db.Column(db.String(10))
    balcony = db.Column(db.String(10))
    loggia = db.Column(db.String(10))
    bathroom = db.Column(db.String(10))
    toilet = db.Column(db.String(10))
    bathroom_combined = db.Column(db.String(10))
    parking = db.Column(db.String(10))
    security = db.Column(db.String(10))
    railway = db.Column(db.String(10))
    with_owners = db.Column(db.String(10))
    joint_ownership = db.Column(db.String(10))
    refrigerator = db.Column(db.String(10))
    tv = db.Column(db.String(10))
    dishwasher = db.Column(db.String(10))
    air_conditioner = db.Column(db.String(10))
    washing_machine = db.Column(db.String(10))
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    clients_count = db.Column(db.Integer)
    views_count = db.Column(db.Integer)
    favorites_count = db.Column(db.Integer)
    operation_id = db.Column(db.Integer)
    created_date = db.Column(db.DateTime)
    modified_date = db.Column(db.DateTime)
    moderation_date = db.Column(db.DateTime)
    activation_date = db.Column(db.DateTime)
    update_date = db.Column(db.DateTime)
    type_id = db.Column(db.Integer)
    subtype_id = db.Column(db.Integer)
    main_type_id = db.Column(db.Integer)
    region_id = db.Column(db.Integer)
    district_id = db.Column(db.Integer)
    point_id = db.Column(db.Integer)
    district_area_id = db.Column(db.Integer)
    subpoint_id = db.Column(db.Integer)
    microdistrict_id = db.Column(db.Integer)
    street_id = db.Column(db.Integer)
    complex_id = db.Column(db.Integer)
    material_id = db.Column(db.Integer)
    developer_id = db.Column(db.Integer)
    source_id = db.Column(db.Integer)
    commercial = db.Column(db.String(10))
    window_id = db.Column(db.Integer)
    condition_id = db.Column(db.Integer)
    gas_id = db.Column(db.Integer)
    heating_id = db.Column(db.Integer)
    sewage_id = db.Column(db.Integer)
    water_id = db.Column(db.Integer)
    electricity_id = db.Column(db.Integer)
    requirement_id = db.Column(db.Integer)
    furniture_id = db.Column(db.Integer)
    land_use_id = db.Column(db.Integer)
    status_id = db.Column(db.Integer)
    balcony_glazing_id = db.Column(db.Integer)
    loggia_glazing_id = db.Column(db.Integer)
    source_url = db.Column(db.String(1000))
    alternative_types = db.Column(db.Text)
    images = db.Column(db.Text)
    contacts = db.Column(db.Text)
    price_per_sqm = db.Column(db.Float)
    # Связь с таблицей адресов
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    dadata_address = db.relationship('Address', backref='properties')


class AntiznakStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), unique=True, nullable=False)
    status = db.Column(db.String(32))
    photos = db.Column(db.Text)  # JSON-строка с массивом локальных путей к фото
    last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error = db.Column(db.Text)
    source_url = db.Column(db.String(1000))
    property = db.relationship('Property', backref=db.backref('antiznak_status', uselist=False))


class ResidentialComplex(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hobj_id = db.Column(db.Integer, unique=True)
    obj_id = db.Column(db.Integer)
    name = db.Column(db.String(255))
    address = db.Column(db.String(255))
    short_address = db.Column(db.String(255))
    developer_name = db.Column(db.String(255))
    developer_full_name = db.Column(db.String(255))
    developer_inn = db.Column(db.String(32))
    min_floor = db.Column(db.Integer)
    max_floor = db.Column(db.Integer)
    ready_date = db.Column(db.String(32))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    status = db.Column(db.String(64))
    build_type = db.Column(db.String(64))
    photo_url = db.Column(db.String(512))
    publ_date = db.Column(db.String(32))
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    dadata_address = db.relationship('Address', backref='complexes')


class YandexNewBuilding(db.Model):
    __tablename__ = 'yandex_newbuildings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    region = db.Column(db.String(255))
    complex_name = db.Column(db.String(255))
    complex_id = db.Column(db.String(64))
    queue = db.Column(db.String(64))
    ready_date = db.Column(db.String(64))
    address = db.Column(db.String(255))
    building_id = db.Column(db.String(64))
    url = db.Column(db.String(512))
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    dadata_address = db.relationship('Address', backref='yandex_newbuildings')


class Lead2CallLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(32))  # success, error
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)


class PropertyRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), unique=True, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    property = db.relationship('Property', backref=db.backref('rating_obj', uselist=False))


class PropertyYandexRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), unique=True, nullable=False)
    yandex_rating = db.Column(db.Integer, nullable=False)
    property = db.relationship('Property', backref=db.backref('yandex_rating_obj', uselist=False))


class PropertyYandexLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), unique=True)
    yandex_complex_name = db.Column(db.String(255))
    property = db.relationship('Property', backref=db.backref('yandex_link', uselist=False))


class PropertyGeneratedDescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), unique=True, nullable=False)
    generated_description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    property = db.relationship('Property', backref=db.backref('generated_description_obj', uselist=False))


class SellerContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(32))
    phone = db.Column(db.String(32))
    name = db.Column(db.String(128))
    comment = db.Column(db.String(512))
    offer = db.Column(db.String(128))
    utm_medium = db.Column(db.String(64))
    utm_source = db.Column(db.String(64))
    utm_term = db.Column(db.String(64))
    audio = db.Column(db.String(512))


# Импорт продавцов из CSV
import requests
import csv

SELLERS_CSV_URL = 'https://docs.google.com/spreadsheets/d/1FslDFa7gKzQ1N6H6txhJuj0tKFV1QuWZVpITsAecsQI/export?format=csv&id=1FslDFa7gKzQ1N6H6txhJuj0tKFV1QuWZVpITsAecsQI&gid=0'


def import_seller_contacts():
    try:
        response = requests.get(SELLERS_CSV_URL, timeout=30)
        response.raise_for_status()
        content = response.content.decode('utf-8')
        reader = csv.DictReader(content.splitlines())
        SellerContact.query.delete()
        for row in reader:
            contact = SellerContact(
                date=row.get('date', ''),
                phone=row.get('phone', ''),
                name=row.get('name', ''),
                comment=row.get('comment', ''),
                offer=row.get('offer', ''),
                utm_medium=row.get('utm_medium', ''),
                utm_source=row.get('utm_source', ''),
                utm_term=row.get('utm_term', ''),
                audio=row.get('audio', '')
            )
            db.session.add(contact)
        db.session.commit()
        return True
    except Exception as e:
        print(f'Ошибка при импорте продавцов: {e}')
        return False


@app.route('/api/import-seller-contacts')
def api_import_seller_contacts():
    success = import_seller_contacts()
    return jsonify({'success': success})


@app.route('/sellers')
def sellers_page():
    return render_template('sellers.html')


@app.route('/api/seller-contacts')
def api_seller_contacts():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '', type=str)
    query = SellerContact.query
    if search:
        query = query.filter(
            SellerContact.phone.ilike(f'%{search}%') |
            SellerContact.name.ilike(f'%{search}%') |
            SellerContact.comment.ilike(f'%{search}%')
        )
    pagination = query.order_by(SellerContact.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for c in pagination.items:
        items.append({
            'id': c.id,
            'date': c.date,
            'phone': c.phone,
            'name': c.name,
            'comment': c.comment,
            'offer': c.offer,
            'utm_medium': c.utm_medium,
            'utm_source': c.utm_source,
            'utm_term': c.utm_term,
            'audio': c.audio
        })
    return jsonify({
        'items': items,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


def parse_date(date_str):
    if pd.isna(date_str) or date_str == '':
        return None
    try:
        return datetime.strptime(str(date_str), '%d.%m.%Y')
    except:
        return None


def clean_numeric(value):
    if pd.isna(value) or value == '':
        return None
    try:
        # Убираем пробелы и заменяем запятую на точку
        cleaned = str(value).replace(' ', '').replace(',', '.')
        return float(cleaned)
    except:
        return None


def get_address_from_coordinates(lat, lon):
    """Получает адрес по координатам через DaData API"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Token {DADATA_API_KEY}'
        }

        payload = {
            'lat': lat,
            'lon': lon,
            'count': 1,
            'radius_meters': 100
        }

        response = requests.post(DADATA_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get('suggestions') and len(data['suggestions']) > 0:
            suggestion = data['suggestions'][0]
            suggestion_data = suggestion.get('data', {})

            return {
                'address': suggestion.get('value', ''),
                'full_address': suggestion.get('unrestricted_value', ''),
                'postal_code': suggestion_data.get('postal_code', ''),
                'country': suggestion_data.get('country', ''),
                'region': suggestion_data.get('region', ''),
                'city': suggestion_data.get('city', ''),
                'street': suggestion_data.get('street', ''),
                'house': suggestion_data.get('house', ''),
                'fias_id': suggestion_data.get('fias_id', None)
            }

        return None
    except Exception as e:
        print(f"Ошибка при получении адреса по координатам: {e}")
        return None


def get_or_create_address(lat, lon):
    """Получает существующий адрес или создает новый"""
    if not lat or not lon:
        return None
    # Получаем адрес через DaData API
    address_data = get_address_from_coordinates(lat, lon)
    if not address_data:
        return None
    fias_id = address_data.get('fias_id')
    if fias_id:
        existing_address = Address.query.filter_by(fias_id=fias_id).first()
        if existing_address:
            return existing_address
    else:
        # Фоллбек: поиск по координатам, если fias_id отсутствует
        existing_address = Address.query.filter_by(latitude=lat, longitude=lon).first()
        if existing_address:
            return existing_address
    # Создаем новый адрес
    new_address = Address(
        latitude=lat,
        longitude=lon,
        dadata_address=address_data['address'],
        dadata_full_address=address_data['full_address'],
        postal_code=address_data['postal_code'],
        country=address_data['country'],
        region=address_data['region'],
        city=address_data['city'],
        street=address_data['street'],
        house=address_data['house'],
        fias_id=fias_id
    )
    db.session.add(new_address)
    db.session.commit()
    return new_address


def load_data_from_csv():
    if os.path.exists('data.csv'):
        df = pd.read_csv('data.csv', sep=';', encoding='utf-8')

        # Счетчики для статистики
        updated_count = 0
        created_count = 0

        for index, row in df.iterrows():
            try:
                site_id = str(row.get('ID на сайте', ''))
                if not site_id:
                    continue

                # Ищем существующую запись по site_id
                existing_property = Property.query.filter_by(site_id=site_id).first()

                # Очищаем description и contacts от nan/None
                def clean_text(val):
                    if pd.isna(val) or str(val).lower() in ['nan', 'none', '<na>']:
                        return ''
                    return str(val)

                # Подготавливаем данные для записи
                property_data = {
                    'site_id': site_id,
                    'description': clean_text(row.get('Описание', '')),
                    'title': str(row.get('Название', '')),
                    'content': str(row.get('Содержание', '')),
                    'note': str(row.get('Примечание', '')),
                    'plot_area': clean_numeric(row.get('Площадь участка')),
                    'min_plot_area': clean_numeric(row.get('Минимальная площадь участка')),
                    'total_area': clean_numeric(row.get('Общая площадь')),
                    'min_area': clean_numeric(row.get('Минимальная площадь')),
                    'living_area': clean_numeric(row.get('Жилая площадь')),
                    'kitchen_area': clean_numeric(row.get('Площадь кухни')),
                    'facade': str(row.get('Фасад', '')),
                    'total_floors': int(row.get('Всего этажей', 0)) if pd.notna(row.get('Всего этажей')) else None,
                    'floor': int(row.get('Этаж', 0)) if pd.notna(row.get('Этаж')) else None,
                    'rooms_count': int(row.get('Количество комнат', 0)) if pd.notna(
                        row.get('Количество комнат')) else None,
                    'isolated_rooms': int(row.get('Изолированные комнаты', 0)) if pd.notna(
                        row.get('Изолированные комнаты')) else None,
                    'total_rooms': int(row.get('Всего комнат', 0)) if pd.notna(row.get('Всего комнат')) else None,
                    'price': clean_numeric(row.get('Цена')),
                    'min_price': clean_numeric(row.get('Минимальная цена')),
                    'address': str(row.get('Адрес', '')),
                    'house': str(row.get('Дом', '')),
                    'building': str(row.get('Строение', '')),
                    'letter': str(row.get('Литер', '')),
                    'landmark': str(row.get('Ориентир', '')),
                    'construction_year': int(row.get('Год постройки', 0)) if pd.notna(
                        row.get('Год постройки')) else None,
                    'delivery_quarter': str(row.get('Квартал сдачи', '')),
                    'house_part': str(row.get('Часть дома', '')),
                    'house_readiness': str(row.get('Готовность дома', '')),
                    'exclusive': str(row.get('Эксклюзив', '')),
                    'balcony': str(row.get('Балкон', '')),
                    'loggia': str(row.get('Лоджия', '')),
                    'bathroom': str(row.get('Ванная', '')),
                    'toilet': str(row.get('Туалет', '')),
                    'bathroom_combined': str(row.get('Санузел', '')),
                    'parking': str(row.get('Парковка', '')),
                    'security': str(row.get('Охрана', '')),
                    'railway': str(row.get('Железная дорога', '')),
                    'with_owners': str(row.get('С собственниками', '')),
                    'joint_ownership': str(row.get('Совместная собственность', '')),
                    'refrigerator': str(row.get('Холодильник', '')),
                    'tv': str(row.get('Телевизор', '')),
                    'dishwasher': str(row.get('Посудомоечная машина', '')),
                    'air_conditioner': str(row.get('Кондиционер', '')),
                    'washing_machine': str(row.get('Стиральная машина', '')),
                    'longitude': clean_numeric(row.get('Долгота')),
                    'latitude': clean_numeric(row.get('Широта')),
                    'clients_count': int(row.get('Количество клиентов', 0)) if pd.notna(
                        row.get('Количество клиентов')) else None,
                    'views_count': int(row.get('Количество просмотров', 0)) if pd.notna(
                        row.get('Количество просмотров')) else None,
                    'favorites_count': int(row.get('Количество в избранном', 0)) if pd.notna(
                        row.get('Количество в избранном')) else None,
                    'operation_id': int(row.get('ID операции', 0)) if pd.notna(row.get('ID операции')) else None,
                    'created_date': parse_date(row.get('Дата создания')),
                    'modified_date': parse_date(row.get('Дата изменения')),
                    'moderation_date': parse_date(row.get('Дата модерации')),
                    'activation_date': parse_date(row.get('Дата активации')),
                    'update_date': parse_date(row.get('Дата обновления')),
                    'type_id': int(row.get('ID типа', 0)) if pd.notna(row.get('ID типа')) else None,
                    'subtype_id': int(row.get('ID подтипа', 0)) if pd.notna(row.get('ID подтипа')) else None,
                    'main_type_id': int(row.get('ID основного типа', 0)) if pd.notna(
                        row.get('ID основного типа')) else None,
                    'region_id': int(row.get('ID региона', 0)) if pd.notna(row.get('ID региона')) else None,
                    'district_id': int(row.get('ID района', 0)) if pd.notna(row.get('ID района')) else None,
                    'point_id': int(row.get('ID точки', 0)) if pd.notna(row.get('ID точки')) else None,
                    'district_area_id': int(row.get('ID округа', 0)) if pd.notna(row.get('ID округа')) else None,
                    'subpoint_id': int(row.get('ID подточки', 0)) if pd.notna(row.get('ID подточки')) else None,
                    'microdistrict_id': int(row.get('ID микрорайона', 0)) if pd.notna(
                        row.get('ID микрорайона')) else None,
                    'street_id': int(row.get('ID улицы', 0)) if pd.notna(row.get('ID улицы')) else None,
                    'complex_id': int(row.get('ID комплекса', 0)) if pd.notna(row.get('ID комплекса')) else None,
                    'material_id': int(row.get('ID материала', 0)) if pd.notna(row.get('ID материала')) else None,
                    'developer_id': int(row.get('ID застройщика', 0)) if pd.notna(row.get('ID застройщика')) else None,
                    'source_id': int(row.get('ID источника', 0)) if pd.notna(row.get('ID источника')) else None,
                    'commercial': str(row.get('Коммерческая', '')),
                    'window_id': int(row.get('ID окна', 0)) if pd.notna(row.get('ID окна')) else None,
                    'condition_id': int(row.get('ID состояния', 0)) if pd.notna(row.get('ID состояния')) else None,
                    'gas_id': int(row.get('ID газа', 0)) if pd.notna(row.get('ID газа')) else None,
                    'heating_id': int(row.get('ID отопления', 0)) if pd.notna(row.get('ID отопления')) else None,
                    'sewage_id': int(row.get('ID канализации', 0)) if pd.notna(row.get('ID канализации')) else None,
                    'water_id': int(row.get('ID воды', 0)) if pd.notna(row.get('ID воды')) else None,
                    'electricity_id': int(row.get('ID электричества', 0)) if pd.notna(
                        row.get('ID электричества')) else None,
                    'requirement_id': int(row.get('ID требования', 0)) if pd.notna(row.get('ID требования')) else None,
                    'furniture_id': int(row.get('ID мебели', 0)) if pd.notna(row.get('ID мебели')) else None,
                    'land_use_id': int(row.get('ID использования земли', 0)) if pd.notna(
                        row.get('ID использования земли')) else None,
                    'status_id': int(row.get('ID статуса', 0)) if pd.notna(row.get('ID статуса')) else None,
                    'balcony_glazing_id': int(row.get('ID остекления балкона', 0)) if pd.notna(
                        row.get('ID остекления балкона')) else None,
                    'loggia_glazing_id': int(row.get('ID остекления лоджии', 0)) if pd.notna(
                        row.get('ID остекления лоджии')) else None,
                    'source_url': str(row.get('URL источника', '')),
                    'alternative_types': str(row.get('Альтернативные типы', '')),
                    'images': str(row.get('Изображения', '')),
                    'contacts': clean_text(row.get('Контакты', '')),
                    'price_per_sqm': clean_numeric(row.get('Цена за м²'))
                }

                if existing_property:
                    # Обновляем существующую запись
                    for key, value in property_data.items():
                        setattr(existing_property, key, value)
                    updated_count += 1
                else:
                    # Создаем новую запись
                    property_item = Property(**property_data)
                    db.session.add(property_item)
                    created_count += 1

            except Exception as e:
                print(f"Error processing row {index}: {e}")
                continue

        db.session.commit()
        print(f"Обновлено записей: {updated_count}, создано новых: {created_count}")

        # Связывание объектов с адресами по координатам (УДАЛЕНО)
        # print("Связывание объектов с адресами...")
        # properties_with_coords = Property.query.filter(
        #     Property.latitude.isnot(None),
        #     Property.longitude.isnot(None),
        #     Property.address_id.is_(None)
        # ).all()
        # 
        # for prop in properties_with_coords:
        #     try:
        #         address = get_or_create_address(prop.latitude, prop.longitude)
        #         if address:
        #             prop.address_id = address.id
        #     except Exception as e:
        #         print(f"Ошибка при связывании объекта {prop.id} с адресом: {e}")
        # 
        # db.session.commit()
        return True
    return False


def download_and_update_data():
    """Скачивает CSV файл и обновляет базу данных"""
    try:
        # Скачиваем CSV файл
        url = "http://81.90.182.151:6050/api/download"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Сохраняем во временный файл
        with open('data.csv', 'wb') as f:
            f.write(response.content)

        # Загружаем данные в базу
        success = load_data_from_csv()
        return success
    except Exception as e:
        print(f"Ошибка при скачивании данных: {e}")
        return False


@app.route('/')
def index():
    return redirect(url_for('admin'))


@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/api/properties')
def get_properties():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    property_id = request.args.get('id', type=int)
    contacts_only = request.args.get('contacts_only', type=int)
    in_complex_only = request.args.get('in_complex_only', type=int)

    # Если запрошен конкретный объект по ID
    if property_id:
        property_item = db.session.get(Property, property_id)
        if property_item:
            # Получаем информацию об адресе
            address_info = None
            if property_item.dadata_address:
                address_info = {
                    'id': property_item.dadata_address.id,
                    'address': property_item.dadata_address.dadata_address,
                    'full_address': property_item.dadata_address.dadata_full_address,
                    'city': property_item.dadata_address.city,
                    'street': property_item.dadata_address.street,
                    'house': property_item.dadata_address.house
                }

            # Проверяем, был ли номер отправлен в КЦ
            sent_to_callcenter = False
            if property_item.contacts:
                import re
                phone_match = re.search(r'(\+?\d{10,15})', property_item.contacts)
                if phone_match:
                    phone = phone_match.group(1)
                    sent_to_callcenter = Lead2CallLog.query.filter_by(phone=phone, status='success').first() is not None
            else:
                sent_to_callcenter = False

            # Найти связанный Яндекс-ЖК по address_id
            yandex_complex_name = None
            if property_item.yandex_link:
                yandex_complex_name = property_item.yandex_link.yandex_complex_name

            # Аналогичные квартиры (same_flats)
            same_flats = []
            if property_item.address_id and property_item.rooms_count:
                flats = Property.query.filter(
                    Property.address_id == property_item.address_id,
                    Property.rooms_count == property_item.rooms_count,
                    Property.id != property_item.id
                ).all()
                # Только с рейтингом
                flats = [flat for flat in flats if getattr(flat, 'rating_obj', None)]
                flats.sort(key=lambda f: f.rating_obj.rating)
                for flat in flats:
                    same_flats.append({
                        'id': flat.id,
                        'address': flat.address,
                        'images': flat.images,
                        'antiznak_photos': [p.replace('\\', '/').replace('\\', '/') for p in
                                            json.loads(flat.antiznak_status.photos)] if getattr(flat, 'antiznak_status',
                                                                                                None) and flat.antiznak_status.photos else [],
                        'price': flat.price,
                        'total_area': flat.total_area,
                        'floor': flat.floor,
                        'total_floors': flat.total_floors,
                        'rating': flat.rating_obj.rating
                    })

            return jsonify({
                'properties': [{
                    'id': property_item.id,
                    'title': property_item.title or 'Без названия',
                    'address': property_item.address or 'Адрес не указан',
                    'price': property_item.price,
                    'total_area': property_item.total_area,
                    'rooms_count': property_item.rooms_count,
                    'floor': property_item.floor,
                    'total_floors': property_item.total_floors,
                    'construction_year': property_item.construction_year,
                    'content': property_item.content or '',
                    'images': property_item.images or '',
                    'contacts': property_item.contacts or '',
                    'price_per_sqm': property_item.price_per_sqm,
                    'longitude': property_item.longitude,
                    'latitude': property_item.latitude,
                    'dadata_address': address_info,
                    'antiznak_photos': [p.replace('\\', '/').replace('\\', '/') for p in
                                        json.loads(property_item.antiznak_status.photos)] if getattr(property_item,
                                                                                                     'antiznak_status',
                                                                                                     None) and property_item.antiznak_status.photos else [],
                    'antiznak_status_status': getattr(property_item.antiznak_status, 'status', None),
                    'source_url': property_item.source_url,
                    'sent_to_callcenter': sent_to_callcenter,
                    'rating': property_item.rating_obj.rating if getattr(property_item, 'rating_obj', None) else None,
                    'yandex_rating': property_item.yandex_rating_obj.yandex_rating if getattr(property_item,
                                                                                              'yandex_rating_obj',
                                                                                              None) else None,
                    'yandex_complex_name': yandex_complex_name,
                    'same_flats': same_flats,
                    'generated_description': property_item.generated_description_obj.generated_description if getattr(
                        property_item, 'generated_description_obj', None) else None
                }],
                'total': 1,
                'pages': 1,
                'current_page': 1,
                'per_page': 1
            })
        else:
            return jsonify({'properties': [], 'total': 0, 'pages': 0, 'current_page': 1, 'per_page': 1})

    # Фильтры
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    area_min = request.args.get('area_min', type=float)
    area_max = request.args.get('area_max', type=float)
    rooms = request.args.get('rooms', type=int)
    address = request.args.get('address', '')
    filter_id = request.args.get('id', type=int)
    yandex_complex = request.args.get('yandex_complex', type=str)
    rating_min = request.args.get('rating_min', type=int)
    rating_max = request.args.get('rating_max', type=int)
    yandex_rating_min = request.args.get('yandex_rating_min', type=int)
    yandex_rating_max = request.args.get('yandex_rating_max', type=int)

    query = Property.query
    if in_complex_only:
        query = query.join(PropertyYandexLink)
    if filter_id is not None:
        query = query.filter(Property.id == filter_id)
    if price_min is not None:
        query = query.filter(Property.price >= price_min)
    if price_max is not None:
        query = query.filter(Property.price <= price_max)
    if area_min is not None:
        query = query.filter(Property.total_area >= area_min)
    if area_max is not None:
        query = query.filter(Property.total_area <= area_max)
    if rooms is not None:
        query = query.filter(Property.rooms_count == rooms)
    if address:
        query = query.filter(Property.address.contains(address))
    if contacts_only:
        query = query.filter(
            Property.contacts.isnot(None),
            Property.contacts != '',
            Property.contacts != 'nan',
            Property.contacts != 'None'
        )
    if yandex_complex:
        # Фильтруем объекты по связанному ЖК через таблицу связей
        query = query.join(PropertyYandexLink).filter(
            PropertyYandexLink.yandex_complex_name.ilike(f'%{yandex_complex}%'))
    if rating_min is not None or rating_max is not None:
        query = query.outerjoin(PropertyRating, Property.id == PropertyRating.property_id)
        if rating_min is not None:
            query = query.filter(PropertyRating.rating >= rating_min)
        if rating_max is not None:
            query = query.filter(PropertyRating.rating <= rating_max)
    if yandex_rating_min is not None or yandex_rating_max is not None:
        query = query.outerjoin(PropertyYandexRating, Property.id == PropertyYandexRating.property_id)
        if yandex_rating_min is not None:
            query = query.filter(PropertyYandexRating.yandex_rating >= yandex_rating_min)
        if yandex_rating_max is not None:
            query = query.filter(PropertyYandexRating.yandex_rating <= yandex_rating_max)

    q = request.args.get('q', '').strip()
    if q:
        import re
        # Если только цифры — ищем и по id, и по контактам, и по адресу, и по ЖК
        if q.isdigit():
            query = query.filter(
                or_(
                    Property.id == int(q),
                    Property.address.ilike(f'%{q}%'),
                    Property.contacts.ilike(f'%{q}%'),
                    PropertyYandexLink.yandex_complex_name.ilike(f'%{q}%')
                )
            ).outerjoin(PropertyYandexLink, Property.id == PropertyYandexLink.property_id)
        else:
            # Поиск по адресу, контактам, ЖК
            query = query.filter(
                or_(
                    Property.address.ilike(f'%{q}%'),
                    Property.contacts.ilike(f'%{q}%'),
                    PropertyYandexLink.yandex_complex_name.ilike(f'%{q}%')
                )
            ).outerjoin(PropertyYandexLink, Property.id == PropertyYandexLink.property_id)

    # Сортировка по ID в порядке убывания (новые сверху)
    query = query.order_by(Property.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    properties = []
    for prop in pagination.items:
        # Получаем информацию об адресе
        address_info = None
        if prop.dadata_address:
            address_info = {
                'id': prop.dadata_address.id,
                'address': prop.dadata_address.dadata_address,
                'full_address': prop.dadata_address.dadata_full_address,
                'city': prop.dadata_address.city,
                'street': prop.dadata_address.street,
                'house': prop.dadata_address.house
            }

        # Проверяем, был ли номер отправлен в КЦ
        sent_to_callcenter = False
        if prop.contacts:
            import re
            phone_match = re.search(r'(\+?\d{10,15})', prop.contacts)
            if phone_match:
                phone = phone_match.group(1)
                sent_to_callcenter = Lead2CallLog.query.filter_by(phone=phone, status='success').first() is not None
        else:
            sent_to_callcenter = False

        # Найти связанный Яндекс-ЖК по address_id
        yandex_complex_name = None
        if prop.yandex_link:
            yandex_complex_name = prop.yandex_link.yandex_complex_name

        # Аналогичные квартиры (same_flats)
        same_flats = []
        if prop.address_id and prop.rooms_count:
            flats = Property.query.filter(
                Property.address_id == prop.address_id,
                Property.rooms_count == prop.rooms_count,
                Property.id != prop.id
            ).all()
            # Только с рейтингом
            flats = [flat for flat in flats if getattr(flat, 'rating_obj', None)]
            flats.sort(key=lambda f: f.rating_obj.rating)
            for flat in flats:
                same_flats.append({
                    'id': flat.id,
                    'address': flat.address,
                    'images': flat.images,
                    'antiznak_photos': [p.replace('\\', '/').replace('\\', '/') for p in
                                        json.loads(flat.antiznak_status.photos)] if getattr(flat, 'antiznak_status',
                                                                                            None) and flat.antiznak_status.photos else [],
                    'price': flat.price,
                    'total_area': flat.total_area,
                    'floor': flat.floor,
                    'total_floors': flat.total_floors,
                    'rating': flat.rating_obj.rating
                })

        properties.append({
            'id': prop.id,
            'title': prop.title or 'Без названия',
            'address': prop.address or 'Адрес не указан',
            'price': prop.price,
            'total_area': prop.total_area,
            'rooms_count': prop.rooms_count,
            'floor': prop.floor,
            'total_floors': prop.total_floors,
            'construction_year': prop.construction_year,
            'content': prop.content or '',
            'images': prop.images or '',
            'contacts': prop.contacts or '',
            'price_per_sqm': prop.price_per_sqm,
            'longitude': prop.longitude,
            'latitude': prop.latitude,
            'dadata_address': address_info,
            'antiznak_photos': [p.replace('\\', '/').replace('\\', '/') for p in
                                json.loads(prop.antiznak_status.photos)] if getattr(prop, 'antiznak_status',
                                                                                    None) and prop.antiznak_status.photos else [],
            'antiznak_status_status': getattr(prop.antiznak_status, 'status', None),
            'source_url': prop.source_url,
            'sent_to_callcenter': sent_to_callcenter,
            'rating': prop.rating_obj.rating if getattr(prop, 'rating_obj', None) else None,
            'yandex_rating': prop.yandex_rating_obj.yandex_rating if getattr(prop, 'yandex_rating_obj', None) else None,
            'yandex_complex_name': yandex_complex_name,
            'same_flats': same_flats,
            'generated_description': prop.generated_description_obj.generated_description if getattr(prop,
                                                                                                     'generated_description_obj',
                                                                                                     None) else None
        })

    return jsonify({
        'properties': properties,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


@app.route('/api/load-data')
def load_data():
    success = load_data_from_csv()
    return jsonify({'success': success})


@app.route('/api/stats')
def get_stats():
    total_properties = Property.query.count()

    import re
    properties_with_phone = Property.query.filter(Property.contacts.isnot(None)).all()
    phone_count = 0
    sent_to_callcenter = 0
    watermarks_removed = 0
    for prop in properties_with_phone:
        if re.search(r'\d{10,15}', prop.contacts or ''):
            phone_count += 1
            phone_match = re.search(r'(\+?\d{10,15})', prop.contacts or '')
            if phone_match:
                phone = phone_match.group(1)
                if Lead2CallLog.query.filter_by(phone=phone, status='success').first():
                    sent_to_callcenter += 1
    # Считаем объекты, у которых водяные знаки удалены
    properties_with_source = Property.query.filter(Property.source_url.isnot(None)).all()
    for prop in properties_with_source:
        status = getattr(prop, 'antiznak_status', None)
        if status and status.status == 'done' and status.photos:
            try:
                photos = json.loads(status.photos)
                if photos:
                    watermarks_removed += 1
            except Exception:
                pass
    # Новые поля
    with_address = Property.query.filter(Property.address_id.isnot(None)).count()
    in_complex = db.session.query(PropertyYandexLink.property_id).count()
    # Новое поле: количество объектов со сгенерированным описанием
    generated_description_count = PropertyGeneratedDescription.query.count()
    return jsonify({
        'total_properties': total_properties,
        'phone_count': phone_count,
        'sent_to_callcenter': sent_to_callcenter,
        'watermarks_removed': watermarks_removed,
        'with_address': with_address,
        'in_complex': in_complex,
        'generated_description_count': generated_description_count
    })


@app.route('/api/download-and-update')
def download_and_update():
    """API endpoint для скачивания и обновления данных"""
    success = download_and_update_data()
    return jsonify({'success': success})


@app.route('/api/geocode-property/<int:property_id>')
def geocode_property(property_id):
    """API endpoint для геокодирования конкретного объекта"""
    try:
        property_item = db.session.get(Property, property_id)
        if not property_item:
            return jsonify({'success': False, 'error': 'Объект не найден'})

        if not property_item.latitude or not property_item.longitude:
            return jsonify({'success': False, 'error': 'Координаты не указаны'})

        # Получаем или создаем адрес
        address = get_or_create_address(property_item.latitude, property_item.longitude)
        if not address:
            return jsonify({'success': False, 'error': 'Не удалось получить адрес'})

        # Связываем объект с адресом
        property_item.address_id = address.id
        db.session.commit()

        return jsonify({
            'success': True,
            'address': {
                'id': address.id,
                'address': address.dadata_address,
                'full_address': address.dadata_full_address,
                'city': address.city,
                'street': address.street,
                'house': address.house
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/geocode-all')
def geocode_all():
    """API endpoint для геокодирования всех объектов без адресов"""
    global STOP_GEOCODING_TASKS
    STOP_GEOCODING_TASKS = False
    try:
        properties_without_address = Property.query.filter(
            Property.latitude.isnot(None),
            Property.longitude.isnot(None),
            Property.address_id.is_(None)
        ).all()
        processed = 0
        errors = 0
        error_403_count = 0
        for prop in properties_without_address:
            if STOP_GEOCODING_TASKS:
                break
            try:
                address = get_or_create_address(prop.latitude, prop.longitude)
                if address:
                    prop.address_id = address.id
                    processed += 1
                else:
                    errors += 1
            except Exception as e:
                if '403' in str(e):
                    error_403_count += 1
                    if error_403_count >= 10:
                        STOP_GEOCODING_TASKS = True
                        break
                errors += 1
        db.session.commit()
        return jsonify({
            'success': not STOP_GEOCODING_TASKS,
            'processed': processed,
            'errors': errors,
            'total': len(properties_without_address),
            'stopped': STOP_GEOCODING_TASKS
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/antiznak/<int:property_id>', methods=['POST'])
def antiznak_remove_watermarks(property_id):
    prop = db.session.get(Property, property_id)
    if not prop:
        return jsonify({'success': False, 'error': 'Объект не найден'})
    if not prop.source_url:
        return jsonify({'success': False, 'error': 'Нет ссылки на объявление'})

    status_obj = AntiznakStatus.query.filter_by(property_id=property_id).first()
    if status_obj and status_obj.status == 'done':
        return jsonify({'success': True, 'status': 'done', 'photos': json.loads(status_obj.photos)})

    url = f"https://antiznak.ru/api/v2.php?k={ANTIZNAK_KEY}&u={requests.utils.quote(prop.source_url)}"
    max_query = 100
    cnt = 0

    while cnt < max_query:
        try:
            resp = requests.get(url, timeout=30)
            data = resp.json()
        except Exception as e:
            return jsonify({'success': False, 'error': f'Ошибка запроса к API: {e}'})
        status = data.get('status')
        if status == 'done':
            photos = list(data.get('photos', {}).values())
            folder = os.path.join('photos', 'antiznak', str(property_id))
            os.makedirs(folder, exist_ok=True)
            local_photos = []
            for i, photo_url in enumerate(photos):
                local_path = os.path.join(folder, f'{i + 1}.jpg')
                try:
                    img = requests.get(photo_url, timeout=30)
                    with open(local_path, 'wb') as f:
                        f.write(img.content)
                    local_photos.append(local_path)
                except Exception as e:
                    continue
            if not status_obj:
                status_obj = AntiznakStatus(property_id=property_id, status='done', photos=json.dumps(local_photos),
                                            source_url=prop.source_url)
                db.session.add(status_obj)
            else:
                status_obj.status = 'done'
                status_obj.photos = json.dumps(local_photos)
                status_obj.error = None
            db.session.commit()
            return jsonify({'success': True, 'status': 'done', 'photos': local_photos})
        elif status == 'error':
            err = data.get('text', 'Ошибка API')
            if not status_obj:
                status_obj = AntiznakStatus(property_id=property_id, status='error', error=err,
                                            source_url=prop.source_url)
                db.session.add(status_obj)
            else:
                status_obj.status = 'error'
                status_obj.error = err
            db.session.commit()
            return jsonify({'success': False, 'status': 'error', 'error': err})
        else:
            # searching или processed XX%
            if not status_obj:
                status_obj = AntiznakStatus(property_id=property_id, status=status, source_url=prop.source_url)
                db.session.add(status_obj)
            else:
                status_obj.status = status
            db.session.commit()
            time.sleep(3)
            cnt += 1
    return jsonify({'success': False, 'status': 'timeout', 'error': 'TimeOut Error!'})


def import_residential_complexes(json_path='object.json'):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = pyjson.load(f)
        complexes = data.get('data', {}).get('list', [])
        ResidentialComplex.query.delete()
        for item in complexes:
            dev = item.get('developer', {})
            org_form = dev.get('orgForm', {})
            rc = ResidentialComplex(
                hobj_id=item.get('hobjId'),
                obj_id=item.get('objId'),
                name=item.get('objCommercNm'),
                address=item.get('objAddr'),
                short_address=item.get('shortAddr'),
                developer_name=dev.get('shortName'),
                developer_full_name=dev.get('fullName'),
                developer_inn=dev.get('devInn'),
                min_floor=item.get('objFloorMin'),
                max_floor=item.get('objFloorMax'),
                ready_date=item.get('objReady100PercDt'),
                latitude=item.get('latitude'),
                longitude=item.get('longitude'),
                status=item.get('siteStatus'),
                build_type=item.get('buildType'),
                photo_url=item.get('hobjRenderPhotoUrl'),
                publ_date=item.get('objPublDt')
            )
            db.session.add(rc)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Ошибка при импорте ЖК: {e}")
        return False


@app.route('/api/import-complexes')
def api_import_complexes():
    try:
        import_residential_complexes()
        return jsonify({'success': True, 'message': 'Импорт ЖК завершен'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/complexes')
def get_complexes():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    name = request.args.get('name', '', type=str)
    developer = request.args.get('developer', '', type=str)
    status = request.args.get('status', '', type=str)

    query = ResidentialComplex.query
    if name:
        query = query.filter(ResidentialComplex.name.ilike(f'%{name}%'))
    if developer:
        query = query.filter(ResidentialComplex.developer_name.ilike(f'%{developer}%'))
    if status:
        query = query.filter(ResidentialComplex.status.ilike(f'%{status}%'))

    pagination = query.order_by(ResidentialComplex.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    complexes = []
    for c in pagination.items:
        complexes.append({
            'id': c.id,
            'hobj_id': c.hobj_id,
            'obj_id': c.obj_id,
            'name': c.name,
            'address': c.address,
            'short_address': c.short_address,
            'developer_name': c.developer_name,
            'developer_full_name': c.developer_full_name,
            'developer_inn': c.developer_inn,
            'min_floor': c.min_floor,
            'max_floor': c.max_floor,
            'ready_date': c.ready_date,
            'latitude': c.latitude,
            'longitude': c.longitude,
            'status': c.status,
            'build_type': c.build_type,
            'photo_url': c.photo_url,
            'publ_date': c.publ_date,
            'dadata_address': {
                'id': c.dadata_address.id,
                'address': c.dadata_address.dadata_address,
                'full_address': c.dadata_address.dadata_full_address,
                'city': c.dadata_address.city,
                'street': c.dadata_address.street,
                'house': c.dadata_address.house
            } if c.dadata_address else None
        })
    return jsonify({
        'complexes': complexes,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


@app.route('/complexes')
def complexes_page():
    return render_template('admin.html')


@app.route('/api/geocode-all-complexes')
def geocode_all_complexes():
    try:
        complexes = ResidentialComplex.query.filter(
            ResidentialComplex.latitude.isnot(None),
            ResidentialComplex.longitude.isnot(None),
            ResidentialComplex.address_id.is_(None)
        ).all()
        processed = 0
        errors = 0
        for c in complexes:
            try:
                address = get_or_create_address(c.latitude, c.longitude)
                if address:
                    c.address_id = address.id
                    processed += 1
                else:
                    errors += 1
            except Exception as e:
                print(f"Ошибка при геокодировании ЖК {c.id}: {e}")
                errors += 1
        db.session.commit()
        return jsonify({
            'success': True,
            'processed': processed,
            'errors': errors,
            'total': len(complexes)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/geocode-complex/<int:complex_id>')
def geocode_complex(complex_id):
    try:
        c = db.session.get(ResidentialComplex, complex_id)
        if not c:
            return jsonify({'success': False, 'error': 'ЖК не найден'})
        if not c.latitude or not c.longitude:
            return jsonify({'success': False, 'error': 'Координаты не указаны'})
        address = get_or_create_address(c.latitude, c.longitude)
        if not address:
            return jsonify({'success': False, 'error': 'Не удалось получить адрес'})
        c.address_id = address.id
        db.session.commit()
        return jsonify({'success': True, 'address': {
            'id': address.id,
            'address': address.dadata_address,
            'full_address': address.dadata_full_address,
            'city': address.city,
            'street': address.street,
            'house': address.house
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/link-properties-complexes')
def link_properties_complexes():
    """API endpoint для связывания объектов и ЖК по адресу"""
    try:
        # Получаем все адреса, которые имеют связанные объекты и ЖК
        addresses_with_both = db.session.query(Address).join(Property).join(ResidentialComplex).distinct().all()

        linked_data = []

        for address in addresses_with_both:
            # Получаем все объекты с этим адресом
            properties = Property.query.filter_by(address_id=address.id).all()

            # Получаем все ЖК с этим адресом
            complexes = ResidentialComplex.query.filter_by(address_id=address.id).all()

            if properties and complexes:
                linked_data.append({
                    'address': {
                        'id': address.id,
                        'address': address.dadata_address,
                        'full_address': address.dadata_full_address,
                        'city': address.city,
                        'street': address.street,
                        'house': address.house,
                        'latitude': address.latitude,
                        'longitude': address.longitude
                    },
                    'properties': [{
                        'id': p.id,
                        'title': p.title or 'Без названия',
                        'address': p.address or 'Адрес не указан',
                        'price': p.price,
                        'total_area': p.total_area,
                        'rooms_count': p.rooms_count,
                        'floor': p.floor,
                        'total_floors': p.total_floors,
                        'construction_year': p.construction_year,
                        'content': p.content or '',
                        'images': p.images or '',
                        'contacts': p.contacts or '',
                        'price_per_sqm': p.price_per_sqm,
                        'longitude': p.longitude,
                        'latitude': p.latitude
                    } for p in properties],
                    'complexes': [{
                        'id': c.id,
                        'name': c.name or 'Без названия',
                        'address': c.address or 'Адрес не указан',
                        'developer_name': c.developer_name or '',
                        'ready_date': c.ready_date or '',
                        'min_floor': c.min_floor,
                        'max_floor': c.max_floor,
                        'status': c.status or '',
                        'photo_url': c.photo_url or '',
                        'longitude': c.longitude,
                        'latitude': c.latitude
                    } for c in complexes]
                })

        return jsonify({
            'success': True,
            'linked_data': linked_data,
            'total_linked_addresses': len(linked_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def import_yandex_newbuildings():
    """Скачивает и импортирует данные из https://realty.yandex.ru/newbuildings.tsv в таблицу yandex_newbuildings"""
    url = 'https://realty.yandex.ru/newbuildings.tsv'
    response = requests.get(url)
    response.raise_for_status()
    content = response.content.decode('utf-8')
    reader = csv.reader(content.splitlines(), delimiter='\t')
    # Очищаем старые данные
    YandexNewBuilding.query.delete()
    for row in reader:
        if len(row) < 8:
            continue
        yb = YandexNewBuilding(
            region=row[0],
            complex_name=row[1],
            complex_id=row[2],
            queue=row[3],
            ready_date=row[4],
            address=row[5],
            building_id=row[6],
            url=row[7]
        )
        db.session.add(yb)
    db.session.commit()
    return True


@app.route('/api/import-yandex-newbuildings')
def api_import_yandex_newbuildings():
    try:
        import_yandex_newbuildings()
        return jsonify({'success': True, 'message': 'Импорт Яндекс-ЖК завершен'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/yandex-newbuildings/regions')
def get_yandex_regions():
    regions = db.session.query(YandexNewBuilding.region).distinct().order_by(YandexNewBuilding.region).all()
    return jsonify([r[0] for r in regions])


@app.route('/api/yandex-newbuildings')
def get_yandex_newbuildings():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '', type=str)
    region = request.args.get('region', '', type=str)
    query = YandexNewBuilding.query
    if region:
        query = query.filter(YandexNewBuilding.region == region)
    if search:
        query = query.filter(YandexNewBuilding.complex_name.ilike(f'%{search}%'))
    pagination = query.order_by(YandexNewBuilding.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for yb in pagination.items:
        items.append({
            'id': yb.id,
            'region': yb.region,
            'complex_name': yb.complex_name,
            'complex_id': yb.complex_id,
            'queue': yb.queue,
            'ready_date': yb.ready_date,
            'address': yb.address,
            'building_id': yb.building_id,
            'url': yb.url,
            'address_id': yb.address_id,
            'dadata_address': yb.dadata_address.dadata_address if yb.dadata_address else None
        })
    return jsonify({
        'items': items,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


@app.route('/yandex-newbuildings')
def yandex_newbuildings_page():
    return render_template('yandex_newbuildings.html')


@app.route('/api/yandex-geocode-region', methods=['POST'])
def yandex_geocode_region():
    global STOP_GEOCODING_TASKS
    STOP_GEOCODING_TASKS = False
    data = request.get_json()
    region = data.get('region')
    if not region:
        return jsonify({'success': False, 'error': 'Регион не указан'})
    buildings = YandexNewBuilding.query.filter_by(region=region).filter(YandexNewBuilding.address_id.is_(None)).all()
    processed = 0
    errors = 0
    error_403_count = 0
    for b in buildings:
        if STOP_GEOCODING_TASKS:
            break
        try:
            address = get_or_create_address_from_string(b.address)
            if address:
                b.address_id = address.id
                processed += 1
            else:
                errors += 1
        except Exception as e:
            if '403' in str(e):
                error_403_count += 1
                if error_403_count >= 10:
                    STOP_GEOCODING_TASKS = True
                    break
            errors += 1
    db.session.commit()
    return jsonify(
        {'success': not STOP_GEOCODING_TASKS, 'processed': processed, 'errors': errors, 'total': len(buildings),
         'stopped': STOP_GEOCODING_TASKS})


@app.route('/api/yandex-geocode-one/<int:building_id>', methods=['POST'])
def yandex_geocode_one(building_id):
    b = YandexNewBuilding.query.get(building_id)
    if not b:
        return jsonify({'success': False, 'error': 'Новостройка не найдена'})
    if b.address_id:
        return jsonify({'success': True, 'message': 'Адрес уже определен', 'address_id': b.address_id})
    address = get_or_create_address_from_string(b.address)
    if address:
        b.address_id = address.id
        db.session.commit()
        return jsonify({'success': True, 'address_id': address.id})
    else:
        return jsonify({'success': False, 'error': 'Не удалось определить адрес'})


def get_or_create_address_from_string(address_str):
    # Используем DaData API для поиска по строке адреса
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Token {DADATA_API_KEY}'
        }
        payload = {
            'query': address_str,
            'count': 1
        }
        url = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address'
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('suggestions') and len(data['suggestions']) > 0:
            suggestion = data['suggestions'][0]
            suggestion_data = suggestion.get('data', {})
            fias_id = suggestion_data.get('fias_id', None)
            geo_lat = suggestion_data.get('geo_lat')
            geo_lon = suggestion_data.get('geo_lon')
            if not geo_lat or not geo_lon:
                return None  # Нет координат — не сохраняем!
            # Поиск по fias_id
            if fias_id:
                existing_address = Address.query.filter_by(fias_id=fias_id).first()
                if existing_address:
                    return existing_address
            # Фоллбек: поиск по строке
            existing_address = Address.query.filter_by(
                dadata_full_address=suggestion.get('unrestricted_value', '')).first()
            if existing_address:
                return existing_address
            # Создаем новый адрес
            new_address = Address(
                latitude=geo_lat,
                longitude=geo_lon,
                dadata_address=suggestion.get('value', ''),
                dadata_full_address=suggestion.get('unrestricted_value', ''),
                postal_code=suggestion_data.get('postal_code', ''),
                country=suggestion_data.get('country', ''),
                region=suggestion_data.get('region', ''),
                city=suggestion_data.get('city', ''),
                street=suggestion_data.get('street', ''),
                house=suggestion_data.get('house', ''),
                fias_id=fias_id
            )
            db.session.add(new_address)
            db.session.commit()
            return new_address
        return None
    except Exception as e:
        print(f"Ошибка при получении адреса по строке: {e}")
        return None


@app.route('/api/stop-all-tasks', methods=['POST'])
def stop_all_tasks():
    global STOP_GEOCODING_TASKS
    STOP_GEOCODING_TASKS = True
    return jsonify({'success': True, 'message': 'Все задачи остановлены'})


@app.route('/api/reset-stop-flag', methods=['POST'])
def reset_stop_flag():
    global STOP_GEOCODING_TASKS
    STOP_GEOCODING_TASKS = False
    return jsonify({'success': True})


@app.route('/api/link-properties-yandex')
def link_properties_yandex():
    try:
        # Получаем все адреса, которые имеют связанные объекты и Яндекс-ЖК
        addresses_with_both = db.session.query(Address).join(Property).join(YandexNewBuilding).distinct().all()
        linked_data = []
        for address in addresses_with_both:
            # Получаем все объекты с этим адресом
            properties = Property.query.filter_by(address_id=address.id).all()
            # Получаем все Яндекс-ЖК с этим адресом
            yandex_newbuildings = YandexNewBuilding.query.filter_by(address_id=address.id).all()
            if properties and yandex_newbuildings:
                linked_data.append({
                    'address': {
                        'id': address.id,
                        'address': address.dadata_address,
                        'full_address': address.dadata_full_address,
                        'city': address.city,
                        'street': address.street,
                        'house': address.house,
                        'latitude': address.latitude,
                        'longitude': address.longitude
                    },
                    'properties': [{
                        'id': p.id,
                        'title': p.title or 'Без названия',
                        'address': p.address or 'Адрес не указан',
                        'price': p.price,
                        'total_area': p.total_area,
                        'rooms_count': p.rooms_count,
                        'floor': p.floor,
                        'total_floors': p.total_floors,
                        'construction_year': p.construction_year,
                        'content': p.content or '',
                        'images': p.images or '',
                        'contacts': p.contacts or '',
                        'price_per_sqm': p.price_per_sqm,
                        'longitude': p.longitude,
                        'latitude': p.latitude
                    } for p in properties],
                    'yandex_newbuildings': [{
                        'id': yb.id,
                        'complex_name': yb.complex_name or 'Без названия',
                        'address': yb.address or 'Адрес не указан',
                        'region': yb.region or '',
                        'ready_date': yb.ready_date or '',
                        'queue': yb.queue or '',
                        'building_id': yb.building_id or '',
                        'url': yb.url or '',
                        'longitude': yb.dadata_address.longitude if yb.dadata_address else None,
                        'latitude': yb.dadata_address.latitude if yb.dadata_address else None
                    } for yb in yandex_newbuildings]
                })
        return jsonify({
            'success': True,
            'linked_data': linked_data,
            'total_linked_addresses': len(linked_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/send-phone', methods=['POST'])
def send_phone():
    data = request.get_json()
    phone = data.get('phone')
    property_id = data.get('property_id')
    if not phone:
        return jsonify({'success': False, 'error': 'Телефон не указан'}), 400
    utm = f"&utm_source=ndv&utm_medium=kirminator2_ndv&utm_term={property_id}" if property_id else ''
    url = f"https://my.lead2call.ru/v2/api/index?token=27f57180-a6cb-46d0-819a-8cd2ab130dab&ident=f6e56c50-acfe-406e-8016-d75527b950a8&phone={phone}{utm}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200 and 'NO PHONE' not in resp.text:
            log = Lead2CallLog(phone=phone, status='success')
            db.session.add(log)
            db.session.commit()
            return jsonify({'success': True})
        else:
            log = Lead2CallLog(phone=phone, status='error', error_message=resp.text)
            db.session.add(log)
            db.session.commit()
            return jsonify({'success': False, 'error': resp.text}), 400
    except Exception as e:
        db.session.rollback()
        log = Lead2CallLog(phone=phone, status='error', error_message=str(e))
        db.session.add(log)
        db.session.commit()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/yandex-linked-complexes')
def get_yandex_linked_complexes():
    # Получить только те complex_name, у которых есть связанные объекты через таблицу связей
    complexes = db.session.query(PropertyYandexLink.yandex_complex_name).distinct().all()
    names = sorted({c[0] for c in complexes if c[0]})
    return jsonify(names)


@app.route('/api/update-ratings', methods=['POST'])
def update_ratings():
    # Удаляем старые рейтинги
    PropertyRating.query.delete()
    db.session.commit()
    # Группируем по адресу
    addresses = Address.query.all()
    for address in addresses:
        # Для каждой группы комнат
        for rooms_group in [1, 2, 3, 4]:
            if rooms_group == 4:
                # 4+ комнаты
                props = Property.query.filter(
                    Property.address_id == address.id,
                    Property.rooms_count >= 4
                ).all()
            else:
                props = Property.query.filter(
                    Property.address_id == address.id,
                    Property.rooms_count == rooms_group
                ).all()
            # Сортируем по цене за м² (по возрастанию)
            props = [p for p in props if p.price_per_sqm]
            props.sort(key=lambda p: p.price_per_sqm)
            # Присваиваем рейтинг
            for idx, prop in enumerate(props):
                rating = idx + 1  # 1 - самое дешёвое
                rating_obj = PropertyRating(property_id=prop.id, rating=rating)
                db.session.add(rating_obj)
    db.session.commit()
    # Для объектов без адреса или комнат — рейтинг максимальный (последний)
    all_ids = {p.id for p in Property.query.all()}
    rated_ids = {r.property_id for r in PropertyRating.query.all()}
    unrated_ids = all_ids - rated_ids
    max_rating = db.session.query(db.func.max(PropertyRating.rating)).scalar() or 1
    for pid in unrated_ids:
        db.session.add(PropertyRating(property_id=pid, rating=max_rating))
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/update-yandex-ratings', methods=['POST'])
def update_yandex_ratings():
    # Удаляем старые ЖК-рейтинги
    PropertyYandexRating.query.delete()
    db.session.commit()
    # Группируем по названию ЖК через таблицу связей
    complex_names = db.session.query(PropertyYandexLink.yandex_complex_name).distinct().all()
    for (complex_name,) in complex_names:
        if not complex_name:
            continue
        # Для каждой группы комнат в этом ЖК
        for rooms_group in [1, 2, 3, 4]:
            if rooms_group == 4:
                # 4+ комнаты
                props = Property.query.join(PropertyYandexLink).filter(
                    PropertyYandexLink.yandex_complex_name == complex_name,
                    Property.rooms_count >= 4
                ).all()
            else:
                props = Property.query.join(PropertyYandexLink).filter(
                    PropertyYandexLink.yandex_complex_name == complex_name,
                    Property.rooms_count == rooms_group
                ).all()
            # Сортируем по цене за м² (по возрастанию)
            props = [p for p in props if p.price_per_sqm]
            props.sort(key=lambda p: p.price_per_sqm)
            # Присваиваем рейтинг
            for idx, prop in enumerate(props):
                rating = idx + 1  # 1 - самое дешёвое
                rating_obj = PropertyYandexRating(property_id=prop.id, yandex_rating=rating)
                db.session.add(rating_obj)
    db.session.commit()
    # Для объектов без ЖК — рейтинг максимальный (последний)
    all_ids = {p.id for p in Property.query.all()}
    rated_ids = {r.property_id for r in PropertyYandexRating.query.all()}
    unrated_ids = all_ids - rated_ids
    max_rating = db.session.query(db.func.max(PropertyYandexRating.yandex_rating)).scalar() or 1
    for pid in unrated_ids:
        db.session.add(PropertyYandexRating(property_id=pid, yandex_rating=max_rating))
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/update-yandex-links', methods=['POST'])
def update_yandex_links():
    # Удаляем старые связи
    PropertyYandexLink.query.delete()
    db.session.commit()
    # Явные JOIN-ы через ON
    links = db.session.query(Property.id, YandexNewBuilding.complex_name) \
        .join(Address, Property.address_id == Address.id) \
        .join(YandexNewBuilding, YandexNewBuilding.address_id == Address.id) \
        .all()
    seen = set()
    for property_id, complex_name in links:
        if property_id in seen:
            continue
        if complex_name:
            link = PropertyYandexLink(property_id=property_id, yandex_complex_name=complex_name)
            db.session.add(link)
            seen.add(property_id)
    db.session.commit()
    return jsonify({'success': True, 'links_created': len(seen)})


@app.route('/api/objects-autocomplete')
def objects_autocomplete():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'id': [], 'address': [], 'complex': [], 'phone': []})
    results = {'id': [], 'address': [], 'complex': [], 'phone': []}
    # Поиск по ID
    if q.isdigit():
        ids = Property.query.filter(Property.id.like(f'%{q}%')).limit(5).all()
        results['id'] = [p.id for p in ids]
    # Поиск по адресу
    addresses = Property.query.filter(Property.address.ilike(f'%{q}%')).limit(5).all()
    results['address'] = list({p.address for p in addresses if p.address})
    # Поиск по ЖК
    complexes = db.session.query(PropertyYandexLink.yandex_complex_name).filter(
        PropertyYandexLink.yandex_complex_name.ilike(f'%{q}%')).limit(5).all()
    results['complex'] = [c[0] for c in complexes if c[0]]
    # Поиск по телефону
    import re
    phone_props = Property.query.filter(Property.contacts.ilike(f'%{q}%')).limit(5).all()
    phones = set()
    for p in phone_props:
        match = re.search(r'(\+?\d{10,15})', p.contacts or '')
        if match:
            phones.add(match.group(1))
    results['phone'] = list(phones)
    return jsonify(results)


@app.route('/api/generate-description/<int:property_id>', methods=['POST'])
def generate_description(property_id):
    """API endpoint для генерации описания объекта недвижимости"""
    try:
        property_item = db.session.get(Property, property_id)
        if not property_item:
            return jsonify({'success': False, 'error': 'Объект не найден'})

        if not property_item.content or property_item.content.strip() == '':
            return jsonify({'success': False, 'error': 'Нет подробного описания для генерации'})

        # Генерируем описание
        generated_text = generate_property_description(property_item.content)
        if not generated_text:
            return jsonify({'success': False, 'error': 'Не удалось сгенерировать описание'})

        # Сохраняем или обновляем в базе
        existing_description = PropertyGeneratedDescription.query.filter_by(property_id=property_id).first()
        if existing_description:
            existing_description.generated_description = generated_text
            existing_description.updated_at = datetime.utcnow()
        else:
            new_description = PropertyGeneratedDescription(
                property_id=property_id,
                generated_description=generated_text
            )
            db.session.add(new_description)

        db.session.commit()

        return jsonify({
            'success': True,
            'generated_description': generated_text
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


class TimeoutException(Exception):
    pass


def timeout(seconds, error_message="Timeout"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = [TimeoutException(error_message)]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    result[0] = e

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            if thread.is_alive():
                raise TimeoutException(error_message)
            if isinstance(result[0], Exception):
                raise result[0]
            return result[0]

        return wrapper

    return decorator


@timeout(10)
def get_response(prompt):
    client = Client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        web_search=False,
        ignore_stream=True
    )
    if re.search('discord.gg', response.choices[0].message.content) or re.search('я не могу помочь',
                                                                                 response.choices[0].message.content):
        return None

    return response


def generate_property_description(content):
    """Генерирует описание объекта недвижимости через gpt4free"""
    if not content or content.strip() == '':
        return None

    prompt = f"""На основе описания {content} создай свое уникальное описание, убери информацию о том что это собственник, и добавь призыв к действию если его нету."""

    try:
        try:
            response = get_response(prompt)
            if not response:
                return generate_property_description(content)

            return response.choices[0].message.content
        except Exception as e:
            print(e)
            return generate_property_description(content)
    except Exception as e:
        print(f"Ошибка при генерации описания: {e}")
        return None


if __name__ == '__main__':
    with app.app_context():
        # Удаляем все таблицы и создаем заново
        db.create_all()

        # Автоматически загружаем данные при первом запуске
        if Property.query.count() == 0:
            load_data_from_csv()

    app.run(debug=True, host='0.0.0.0', port=5000)
