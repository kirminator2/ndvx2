import functools
import signal
import threading

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
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
from sqlalchemy import or_, func
# from g4f.client import Client
from io import StringIO
import traceback
import urllib.parse

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:8080", "http://localhost:3000", "http://127.0.0.1:8080", "http://127.0.0.1:3000"]}})
import os
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.dirname(__file__), "instance", "real_estate.db")}'
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
    slug = db.Column(db.String(255), unique=True)  # Красивый URL для адреса
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи с ЖК
    residential_complex_id = db.Column(db.Integer, db.ForeignKey('residential_complex.id'))
    yandex_complex_id = db.Column(db.Integer, db.ForeignKey('yandex_newbuildings.id'))
    trend_building_id = db.Column(db.String, db.ForeignKey('trend_buildings.id'))
    
    # Отношения
    residential_complex = db.relationship('ResidentialComplex', foreign_keys=[residential_complex_id])
    yandex_complex = db.relationship('YandexNewBuilding', foreign_keys=[yandex_complex_id])
    trend_building = db.relationship('TrendBuilding', foreign_keys=[trend_building_id])


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
    
    # Связи с ЖК
    residential_complex_id = db.Column(db.Integer, db.ForeignKey('residential_complex.id'))
    yandex_complex_id = db.Column(db.Integer, db.ForeignKey('yandex_newbuildings.id'))
    trend_building_id = db.Column(db.Integer, db.ForeignKey('trend_buildings.id'))

    # Отношения с ЖК
    residential_complex = db.relationship('ResidentialComplex', foreign_keys=[residential_complex_id])
    yandex_complex = db.relationship('YandexNewBuilding', foreign_keys=[yandex_complex_id])
    trend_building = db.relationship('TrendBuilding', foreign_keys=[trend_building_id])


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
    dadata_address = db.relationship('Address', foreign_keys=[address_id], backref='complexes')


class ComplexPhoto(db.Model):
    __tablename__ = 'complex_photos'
    id = db.Column(db.Integer, primary_key=True)
    complex_id = db.Column(db.Integer, db.ForeignKey('residential_complex.id'), nullable=False)
    photo_path = db.Column(db.String(512), nullable=False)  # Путь к файлу
    photo_url = db.Column(db.String(512))  # URL фотографии
    title = db.Column(db.String(255))  # Название/описание фото
    is_main = db.Column(db.Boolean, default=False)  # Главное фото
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    complex = db.relationship('ResidentialComplex', backref='photos')


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
    slug = db.Column(db.String(255), unique=True)  # Красивый URL
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    dadata_address = db.relationship('Address', foreign_keys=[address_id], backref='yandex_newbuildings')
    
    # Связи с trend_buildings и trend_blocks
    trend_building_id = db.Column(db.String(64))
    trend_block_id = db.Column(db.String(64))
    
    # Отношения с trend_buildings и trend_blocks
    trend_building = db.relationship('TrendBuilding', foreign_keys=[trend_building_id], primaryjoin="YandexNewBuilding.trend_building_id == TrendBuilding.id")
    trend_block = db.relationship('TrendBlock', foreign_keys=[trend_block_id], primaryjoin="YandexNewBuilding.trend_block_id == TrendBlock.id")


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
    yandex_building_id = db.Column(db.Integer, db.ForeignKey('yandex_newbuildings.id'))
    yandex_complex_name = db.Column(db.String(255))  # Добавляем поле для имени комплекса
    slug = db.Column(db.String(255))  # Красивый URL для ЖК
    property = db.relationship('Property', backref=db.backref('yandex_link', uselist=False))
    yandex_building = db.relationship('YandexNewBuilding', backref=db.backref('property_links'))


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
    
    # Создаем slug для нового адреса
    slug = create_slug_for_address(new_address)
    if slug:
        new_address.slug = slug
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
                    # Сохраняем старую цену для отслеживания изменений
                    old_price = existing_property.price
                    
                    # Обновляем существующую запись
                    for key, value in property_data.items():
                        setattr(existing_property, key, value)
                    
                    # Логируем изменение цены
                    check_and_log_price_change(existing_property, old_price, "csv_import")
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
        # Перенос контактов в новую таблицу после импорта
        migrate_property_contacts()
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

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/bulk-operations')
def bulk_operations():
    return render_template('bulk-operations.html')


@app.route('/api/properties')
def get_properties():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    property_id = request.args.get('id', type=int)
    contacts_only = request.args.get('contacts_only', type=int)
    in_complex_only = request.args.get('in_complex_only', type=int)
    in_sale_only = request.args.get('in_sale_only', type=int)

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
    if in_sale_only:
        # Фильтруем объекты, которые есть в продаже (есть связь с продавцами через UTM Term)
        # Получаем все UTM Term из продавцов, которые не пустые
        utm_terms = db.session.query(SellerContact.utm_term)\
            .filter(SellerContact.utm_term.isnot(None))\
            .filter(SellerContact.utm_term != '')\
            .all()
        
        # Преобразуем в список ID объектов
        property_ids = []
        for (utm_term,) in utm_terms:
            try:
                property_ids.append(int(utm_term))
            except (ValueError, TypeError):
                continue
        
        if property_ids:
            query = query.filter(Property.id.in_(property_ids))
        else:
            # Если нет валидных ID, возвращаем пустой результат
            query = query.filter(Property.id == -1)
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
            )
        else:
            # Поиск по адресу, контактам, ЖК
            query = query.filter(
                or_(
                    Property.address.ilike(f'%{q}%'),
                    Property.contacts.ilike(f'%{q}%'),
                    PropertyYandexLink.yandex_complex_name.ilike(f'%{q}%')
                )
            )

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

        # Проверяем, есть ли объект в продаже (есть ли связь с продавцами)
        in_sale = SellerContact.query.filter(
            SellerContact.utm_term == str(prop.id)
        ).first() is not None

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
            'in_sale': in_sale,
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
    # Новое поле: количество объектов в продаже
    utm_terms = db.session.query(SellerContact.utm_term)\
        .filter(SellerContact.utm_term.isnot(None))\
        .filter(SellerContact.utm_term != '')\
        .all()
    
    property_ids = []
    for (utm_term,) in utm_terms:
        try:
            property_ids.append(int(utm_term))
        except (ValueError, TypeError):
            continue
    
    in_sale_count = Property.query.filter(Property.id.in_(property_ids)).count() if property_ids else 0
    return jsonify({
        'total_properties': total_properties,
        'phone_count': phone_count,
        'sent_to_callcenter': sent_to_callcenter,
        'watermarks_removed': watermarks_removed,
        'with_address': with_address,
        'in_complex': in_complex,
        'generated_description_count': generated_description_count,
        'in_sale_count': in_sale_count
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


@app.route('/api/geocode-all', methods=['GET', 'POST'])
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
        
        total = len(properties_without_address)
        print(f"🚀 Начинаем геокодирование объектов недвижимости. Всего найдено: {total}")
        
        if total == 0:
            print("✅ Нет объектов для геокодирования (все уже имеют адреса)")
            return jsonify({
                'success': True,
                'processed': 0,
                'errors': 0,
                'total': 0,
                'stopped': False
            })
        
        processed = 0
        errors = 0
        error_403_count = 0
        
        for i, prop in enumerate(properties_without_address, 1):
            if STOP_GEOCODING_TASKS:
                print(f"⏹️ Геокодирование остановлено пользователем на {i}/{total}")
                break
                
            try:
                print(f"📍 Обрабатываем объект {prop.id} ({prop.title or 'Без названия'}) - {i}/{total}")
                address = get_or_create_address(prop.latitude, prop.longitude)
                if address:
                    prop.address_id = address.id
                    processed += 1
                    print(f"✅ Объект {prop.id} успешно геокодирован: {address.dadata_address}")
                else:
                    errors += 1
                    print(f"❌ Объект {prop.id} - не удалось получить адрес")
            except Exception as e:
                if '403' in str(e):
                    error_403_count += 1
                    print(f"⚠️ Ошибка 403 для объекта {prop.id} (попытка {error_403_count}/10)")
                    if error_403_count >= 10:
                        STOP_GEOCODING_TASKS = True
                        print("🛑 Превышен лимит ошибок 403, останавливаем геокодирование")
                        break
                else:
                    print(f"❌ Ошибка при геокодировании объекта {prop.id}: {e}")
                errors += 1
        
        db.session.commit()
        
        if STOP_GEOCODING_TASKS:
            print(f"⏹️ Геокодирование остановлено. Обработано: {processed}, ошибок: {errors}")
        else:
            print(f"🎉 Геокодирование завершено!")
            print(f"📊 Результаты: обработано {processed}, ошибок {errors}, всего {total}")
        
        return jsonify({
            'success': not STOP_GEOCODING_TASKS,
            'processed': processed,
            'errors': errors,
            'total': total,
            'stopped': STOP_GEOCODING_TASKS
        })
    except Exception as e:
        print(f"💥 Критическая ошибка при геокодировании: {e}")
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
    return render_template('complexes.html')


@app.route('/api/geocode-all-complexes', methods=['GET', 'POST'])
def geocode_all_complexes():
    print("🎯 Эндпоинт /api/geocode-all-complexes вызван!")
    print(f"📝 Метод запроса: {request.method}")
    try:
        complexes = ResidentialComplex.query.filter(
            ResidentialComplex.latitude.isnot(None),
            ResidentialComplex.longitude.isnot(None),
            ResidentialComplex.address_id.is_(None)
        ).all()
        
        total = len(complexes)
        print(f"🚀 Начинаем геокодирование ЖК. Всего найдено: {total}")
        
        if total == 0:
            print("✅ Нет ЖК для геокодирования (все уже имеют адреса)")
            return jsonify({
                'success': True,
                'processed': 0,
                'errors': 0,
                'total': 0
            })
        
        processed = 0
        errors = 0
        
        for i, c in enumerate(complexes, 1):
            try:
                print(f"📍 Обрабатываем ЖК {c.id} ({c.name or 'Без названия'}) - {i}/{total}")
                address = get_or_create_address(c.latitude, c.longitude)
                if address:
                    c.address_id = address.id
                    processed += 1
                    print(f"✅ ЖК {c.id} успешно геокодирован: {address.dadata_address}")
                else:
                    errors += 1
                    print(f"❌ ЖК {c.id} - не удалось получить адрес")
            except Exception as e:
                print(f"❌ Ошибка при геокодировании ЖК {c.id}: {e}")
                errors += 1
        
        db.session.commit()
        
        print(f"🎉 Геокодирование завершено!")
        print(f"📊 Результаты: обработано {processed}, ошибок {errors}, всего {total}")
        
        return jsonify({
            'success': True,
            'processed': processed,
            'errors': errors,
            'total': total
        })
    except Exception as e:
        print(f"💥 Критическая ошибка при геокодировании: {e}")
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
    
    # Создаем словарь существующих записей для быстрого поиска
    existing_buildings = {}
    for building in YandexNewBuilding.query.all():
        # Используем комбинацию complex_id + building_id как уникальный ключ
        key = f"{building.complex_id}_{building.building_id}"
        existing_buildings[key] = building
    
    added_count = 0
    updated_count = 0
    
    for row in reader:
        if len(row) < 8:
            continue
        
        complex_id = row[2]
        building_id = row[6]
        key = f"{complex_id}_{building_id}"
        
        if key in existing_buildings:
            # Обновляем существующую запись
            building = existing_buildings[key]
            building.region = row[0]
            building.complex_name = row[1]
            building.queue = row[3]
            building.ready_date = row[4]
            building.address = row[5]
            building.url = row[7]
            updated_count += 1
        else:
            # Создаем новую запись
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
            added_count += 1
    
    db.session.commit()
    return True, added_count, updated_count


@app.route('/api/import-yandex-newbuildings', methods=['GET', 'POST'])
def api_import_yandex_newbuildings():
    try:
        success, added_count, updated_count = import_yandex_newbuildings()
        return jsonify({
            'success': success,
            'added_count': added_count,
            'updated_count': updated_count,
            'message': 'Импорт Яндекс-ЖК завершен'
        })
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
    # Используем JOIN для оптимизации подсчета связей
    buildings_with_counts = db.session.query(
        YandexNewBuilding,
        db.func.count(PropertyYandexLink.id).label('linked_count')
    ).outerjoin(PropertyYandexLink, YandexNewBuilding.id == PropertyYandexLink.yandex_building_id)
    
    # Применяем фильтры
    if region:
        buildings_with_counts = buildings_with_counts.filter(YandexNewBuilding.region == region)
    if search:
        buildings_with_counts = buildings_with_counts.filter(YandexNewBuilding.complex_name.ilike(f'%{search}%'))
    
    # Группируем и сортируем
    buildings_with_counts = buildings_with_counts.group_by(YandexNewBuilding.id).order_by(
        db.desc(db.func.count(PropertyYandexLink.id)),
        db.desc(YandexNewBuilding.id)
    )
    
    # Получаем общее количество для пагинации
    total = buildings_with_counts.count()
    pages = (total + per_page - 1) // per_page
    
    # Применяем пагинацию
    paginated_buildings = buildings_with_counts.offset((page - 1) * per_page).limit(per_page).all()
    items = []
    for yb, linked_count in paginated_buildings:
        # Проверяем, есть ли связанный ЖК с фотографиями
        complex_photos = []
        complex_name = None
        linked_complex_id = None
        
        # Ищем ЖК с фотографиями по названию
        if yb.complex_name:
            complex_obj = ResidentialComplex.query.filter(
                ResidentialComplex.name.ilike(f'%{yb.complex_name}%'),
                ResidentialComplex.photo_url.isnot(None),
                ResidentialComplex.photo_url != ''
            ).first()
            if complex_obj:
                complex_name = complex_obj.name
                linked_complex_id = complex_obj.id
                complex_photos = [{
                    'id': complex_obj.id,
                    'photo_path': complex_obj.photo_url,
                    'photo_url': complex_obj.photo_url,
                    'title': f'Фото ЖК {complex_obj.name}',
                    'is_main': True
                }]
        
        # Также ищем ЖК по адресу для получения ID
        if yb.address_id and not linked_complex_id:
            address_complex = ResidentialComplex.query.filter_by(address_id=yb.address_id).first()
            if address_complex:
                linked_complex_id = address_complex.id
                if not complex_name:
                    complex_name = address_complex.name
        
        # Используем уже подсчитанное количество связей
        linked_properties_count = linked_count or 0
        
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
            'dadata_address': yb.dadata_address.dadata_address if yb.dadata_address else None,
            'linked_complex_name': complex_name,
            'linked_complex_id': linked_complex_id,
            'complex_photos': complex_photos,
            'linked_properties_count': linked_properties_count
        })
    return jsonify({
        'items': items,
        'total': total,
        'pages': pages,
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


def generate_slug(text):
    """Генерирует slug из текста (транслитерация + очистка)"""
    import re
    import unicodedata
    
    # Транслитерация кириллицы
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    # Транслитерация
    for cyr, lat in translit_map.items():
        text = text.replace(cyr, lat)
    
    # Нормализация Unicode
    text = unicodedata.normalize('NFKD', text)
    
    # Замена спецсимволов на дефисы
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # Удаление начальных и конечных дефисов
    text = text.strip('-')
    
    # Приведение к нижнему регистру
    text = text.lower()
    
    return text


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
            
            # Создаем slug для нового адреса
            slug = create_slug_for_address(new_address)
            if slug:
                new_address.slug = slug
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
        # Получаем ID объектов "В продаже" из таблицы SellerContact
        utm_terms = db.session.query(SellerContact.utm_term)\
            .filter(SellerContact.utm_term.isnot(None))\
            .filter(SellerContact.utm_term != '')\
            .all()
        
        property_ids_in_sale = []
        for (utm_term,) in utm_terms:
            try:
                property_ids_in_sale.append(int(utm_term))
            except (ValueError, TypeError):
                continue
        
        # Получаем все адреса, которые имеют связанные объекты "В продаже" и Яндекс-ЖК
        if property_ids_in_sale:
            addresses_with_both = db.session.query(Address)\
                .join(Property)\
                .join(YandexNewBuilding)\
                .filter(Property.id.in_(property_ids_in_sale))\
                .distinct().all()
        else:
            addresses_with_both = []
        
        linked_data = []
        for address in addresses_with_both:
            # Получаем только объекты "В продаже" с этим адресом
            properties = Property.query.filter(
                Property.address_id == address.id,
                Property.id.in_(property_ids_in_sale)
            ).all()
            
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
    linked_complexes = db.session.query(YandexNewBuilding.complex_name).join(
        PropertyYandexLink, YandexNewBuilding.complex_name == PropertyYandexLink.yandex_complex_name
    ).distinct().all()
    return jsonify([c[0] for c in linked_complexes])


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
    # Получаем существующие связи для проверки
    existing_links = {}
    for link in PropertyYandexLink.query.all():
        existing_links[link.property_id] = link
    
    # Явные JOIN-ы через ON с получением названия комплекса
    links = db.session.query(Property.id, YandexNewBuilding.id, YandexNewBuilding.complex_name) \
        .join(Address, Property.address_id == Address.id) \
        .join(YandexNewBuilding, YandexNewBuilding.address_id == Address.id) \
        .all()
    
    new_links_count = 0
    updated_links_count = 0
    
    for property_id, yandex_building_id, complex_name in links:
        if yandex_building_id:
            if property_id in existing_links:
                # Обновляем существующую связь
                link = existing_links[property_id]
                link.yandex_building_id = yandex_building_id
                link.yandex_complex_name = complex_name
                updated_links_count += 1
            else:
                # Создаем новую связь
                link = PropertyYandexLink(
                    property_id=property_id, 
                    yandex_building_id=yandex_building_id,
                    yandex_complex_name=complex_name
                )
                db.session.add(link)
                new_links_count += 1
    
    db.session.commit()
    
    # Создаем slug'и для новых связей
    if new_links_count > 0:
        create_slugs_for_yandex_links()
    
    return jsonify({
        'success': True, 
        'new_links_created': new_links_count,
        'existing_links_updated': updated_links_count
    })


def create_slugs_for_yandex_links():
    """Создает slug'и для связей Яндекс-ЖК, у которых их нет"""
    links_without_slugs = PropertyYandexLink.query.filter(
        (PropertyYandexLink.slug.is_(None)) | (PropertyYandexLink.slug == '')
    ).all()
    
    created_count = 0
    for link in links_without_slugs:
        if link.yandex_complex_name:
            # Генерируем slug из названия комплекса
            slug = generate_slug(link.yandex_complex_name)
            
            # Проверяем уникальность в таблице связей
            counter = 1
            original_slug = slug
            while PropertyYandexLink.query.filter_by(slug=slug).first():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            # Обновляем slug
            link.slug = slug
            created_count += 1
    
    db.session.commit()
    return created_count


@app.route('/api/create-yandex-link-slugs', methods=['POST'])
def api_create_yandex_link_slugs():
    """API endpoint для создания slug'ов для связей Яндекс-ЖК"""
    try:
        created_count = create_slugs_for_yandex_links()
        return jsonify({
            'success': True,
            'created_count': created_count,
            'message': f'Создано {created_count} slug\'ов для связей Яндекс-ЖК'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


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
    # Поиск по ЖК — сгруппировать и посчитать количество квартир, вернуть id
    complexes = db.session.query(YandexNewBuilding.id, YandexNewBuilding.complex_name, db.func.count(Property.id)).join(PropertyYandexLink, YandexNewBuilding.id == PropertyYandexLink.yandex_building_id).join(Property, PropertyYandexLink.property_id == Property.id).filter(YandexNewBuilding.complex_name.ilike(f'%{q}%')).group_by(YandexNewBuilding.id, YandexNewBuilding.complex_name).limit(10).all()
    results['complex'] = [{'id': c[0], 'name': c[1], 'count': c[2]} for c in complexes if c[1]]
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
    # client = Client()
    # response = client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[{"role": "user", "content": prompt}],
    #     web_search=False,
    #     ignore_stream=True
    # )
    # if re.search('discord.gg', response.choices[0].message.content) or re.search('я не могу помочь',
    #                                                                              response.choices[0].message.content):
    #     return None

    # return response
    return None  # Временно отключено


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


class PropertyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    contact = db.Column(db.Text)  # Оригинальная строка контакта
    phone = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(128))
    property = db.relationship('Property', backref='contacts_list')


def migrate_property_contacts():
    import re
    PropertyContact.query.delete()
    db.session.commit()
    properties = Property.query.all()
    for prop in properties:
        if not prop.contacts:
            continue
        # Разделяем по |
        blocks = [b.strip() for b in prop.contacts.split('|') if b.strip()]
        used_phones = set()
        for block in blocks:
            # Внутри блока ищем все Имя: ... и Телефон: ...
            name_matches = re.findall(r'Имя[:\s]*([\wА-Яа-яЁё\- ]+)', block)
            phone_matches = re.findall(r'(\d{10,15})', block)
            # Если есть и имя, и телефон — связываем их по порядку
            if phone_matches:
                for idx, phone in enumerate(phone_matches):
                    if phone in used_phones:
                        continue
                    name = name_matches[idx] if idx < len(name_matches) else None
                    contact_str = block  # сохраняем исходный блок
                    contact_obj = PropertyContact(
                        property_id=prop.id,
                        contact=contact_str,
                        phone=phone,
                        name=name
                    )
                    db.session.add(contact_obj)
                    used_phones.add(phone)
    db.session.commit()


@app.route('/api/migrate-property-contacts', methods=['POST'])
def api_migrate_property_contacts():
    try:
        migrate_property_contacts()
        return jsonify({'success': True, 'message': 'Миграция контактов завершена'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


class TrendRoom(db.Model):
    __tablename__ = 'trend_rooms'
    id = db.Column(db.String, primary_key=True)  # _id
    name = db.Column(db.String)
    crm_id = db.Column(db.String)

class TrendBuilder(db.Model):
    __tablename__ = 'trend_builders'
    id = db.Column(db.String, primary_key=True)  # _id
    name = db.Column(db.String)
    crm_id = db.Column(db.String)

class TrendBuildingType(db.Model):
    __tablename__ = 'trend_buildingtypes'
    id = db.Column(db.String, primary_key=True)  # _id
    name = db.Column(db.String)
    crm_id = db.Column(db.String)

class TrendFinishing(db.Model):
    __tablename__ = 'trend_finishings'
    id = db.Column(db.String, primary_key=True)  # _id
    name = db.Column(db.String)
    crm_id = db.Column(db.String)

class TrendSubway(db.Model):
    __tablename__ = 'trend_subways'
    id = db.Column(db.String, primary_key=True)  # _id
    name = db.Column(db.String)
    crm_id = db.Column(db.String)

class TrendRegion(db.Model):
    __tablename__ = 'trend_regions'
    id = db.Column(db.String, primary_key=True)  # _id
    name = db.Column(db.String)
    crm_id = db.Column(db.String)

class TrendBlock(db.Model):
    __tablename__ = 'trend_blocks'
    id = db.Column(db.String, primary_key=True)  # _id
    name = db.Column(db.String)
    crm_id = db.Column(db.String)
    district = db.Column(db.String)  # foreign key to region or district if needed
    description = db.Column(db.Text)
    # Адрес (JSON)
    address = db.Column(db.Text)  # JSON-строка (список)
    # Рендерер и план (JSON)
    renderer = db.Column(db.Text)  # JSON-строка (список)
    plan = db.Column(db.Text)  # JSON-строка (список)
    # Метро (JSON)
    subway = db.Column(db.Text)  # JSON-строка (список)
    # Геометрия (JSON)
    geometry_type = db.Column(db.String)
    geometry_coordinates = db.Column(db.Text)  # JSON-строка

# Для apartments и buildings только структура:
class TrendApartment(db.Model):
    __tablename__ = 'trend_apartments'
    id = db.Column(db.String, primary_key=True)  # _id
    area_balconies_total = db.Column(db.Float)
    area_given = db.Column(db.Float)
    area_kitchen = db.Column(db.Float)
    area_rooms = db.Column(db.String)
    area_rooms_total = db.Column(db.Float)
    area_total = db.Column(db.Float)
    block_address = db.Column(db.String)
    block_builder = db.Column(db.String)
    block_builder_name = db.Column(db.String)
    block_city = db.Column(db.String)
    block_crm_id = db.Column(db.String)
    block_district = db.Column(db.String)
    block_district_name = db.Column(db.String)
    block_geometry_type = db.Column(db.String)
    block_geometry_coordinates = db.Column(db.Text)  # JSON-строка
    block_id = db.Column(db.String)
    block_iscity = db.Column(db.Boolean)
    block_name = db.Column(db.String)
    block_renderer = db.Column(db.Text)  # JSON-строка (список)
    block_subway = db.Column(db.Text)    # JSON-строка (список)
    block_subway_name = db.Column(db.Text)  # JSON-строка (список)
    building_bank = db.Column(db.Text)   # JSON-строка (список)
    building_contract = db.Column(db.Text)  # JSON-строка (список)
    building_deadline = db.Column(db.String)
    building_id = db.Column(db.String)
    building_installment = db.Column(db.Boolean)
    building_mortgage = db.Column(db.Boolean)
    building_name = db.Column(db.String)
    building_queue = db.Column(db.String)
    building_subsidy = db.Column(db.Boolean)
    building_type = db.Column(db.String)
    building_voen_mortgage = db.Column(db.Boolean)
    finishing = db.Column(db.String)
    floor = db.Column(db.Integer)
    floors = db.Column(db.Integer)
    height = db.Column(db.Float)
    number = db.Column(db.String)
    plan = db.Column(db.Text)  # JSON-строка (список)
    price = db.Column(db.Float)
    room = db.Column(db.Integer)
    wc_count = db.Column(db.Integer)

class TrendBuilding(db.Model):
    __tablename__ = 'trend_buildings'
    id = db.Column(db.String, primary_key=True)  # _id
    crm_id = db.Column(db.String)
    name = db.Column(db.String)
    block_id = db.Column(db.String)
    building_type = db.Column(db.String)
    queue = db.Column(db.Integer)
    subsidy = db.Column(db.Boolean)
    deadline = db.Column(db.String)
    deadline_key = db.Column(db.String)
    # Адрес (JSON)
    address_street = db.Column(db.String)
    address_house = db.Column(db.String)
    address_housing = db.Column(db.String)
    address_street_en = db.Column(db.String)
    address_house_en = db.Column(db.String)
    address_housing_en = db.Column(db.String)
    # Геометрия (JSON)
    geometry_type = db.Column(db.String)
    geometry_coordinates = db.Column(db.Text)  # JSON-строка
    # Новое поле для связи с Address
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    dadata_address = db.relationship('Address', foreign_keys=[address_id], backref='trend_buildings')

def import_trendagent_jsons():
    import json
    # Импорт rooms.json (без удаления, с обновлением)
    with open('trendagent/krd/rooms.json', encoding='utf-8') as f:
        for item in json.load(f):
            r = TrendRoom.query.get(item['_id'])
            if r:
                r.name = item.get('name')
                r.crm_id = item.get('crm_id')
            else:
                db.session.add(TrendRoom(id=item['_id'], name=item.get('name'), crm_id=item.get('crm_id')))
    
    # Импорт builders.json (без удаления, с обновлением)
    with open('trendagent/krd/builders.json', encoding='utf-8') as f:
        for item in json.load(f):
            b = TrendBuilder.query.get(item['_id'])
            if b:
                b.name = item.get('name')
                b.crm_id = str(item.get('crm_id')) if item.get('crm_id') is not None else None
            else:
                db.session.add(TrendBuilder(
                    id=item['_id'],
                    name=item.get('name'),
                    crm_id=str(item.get('crm_id')) if item.get('crm_id') is not None else None
                ))
    
    # Импорт buildingtypes.json (без удаления, с обновлением)
    with open('trendagent/krd/buildingtypes.json', encoding='utf-8') as f:
        for item in json.load(f):
            bt = TrendBuildingType.query.get(item['_id'])
            if bt:
                bt.name = item.get('name')
                bt.crm_id = item.get('crm_id')
            else:
                db.session.add(TrendBuildingType(id=item['_id'], name=item.get('name'), crm_id=item.get('crm_id')))
    
    # Импорт finishings.json (без удаления, с обновлением)
    with open('trendagent/krd/finishings.json', encoding='utf-8') as f:
        for item in json.load(f):
            f = TrendFinishing.query.get(item['_id'])
            if f:
                f.name = item.get('name')
                f.crm_id = item.get('crm_id')
            else:
                db.session.add(TrendFinishing(id=item['_id'], name=item.get('name'), crm_id=item.get('crm_id')))
    
    # Импорт subways.json (без удаления, с обновлением)
    with open('trendagent/krd/subways.json', encoding='utf-8') as f:
        for item in json.load(f):
            s = TrendSubway.query.get(item['_id'])
            if s:
                s.name = item.get('name')
                s.crm_id = item.get('crm_id')
            else:
                db.session.add(TrendSubway(id=item['_id'], name=item.get('name'), crm_id=item.get('crm_id')))
    
    # Импорт regions.json (без удаления, с обновлением)
    with open('trendagent/krd/regions.json', encoding='utf-8') as f:
        for item in json.load(f):
            r = TrendRegion.query.get(item['_id'])
            if r:
                r.name = item.get('name')
                r.crm_id = item.get('crm_id')
            else:
                db.session.add(TrendRegion(id=item['_id'], name=item.get('name'), crm_id=item.get('crm_id')))
    # Импорт blocks.json (без удаления, с обновлением)
    with open('trendagent/krd/blocks.json', encoding='utf-8') as f:
        for item in json.load(f):
            b = TrendBlock.query.get(item['_id'])
            if b:
                # Обновляем существующую запись
                b.name = item.get('name')
                b.crm_id = item.get('crm_id')
                b.district = item.get('district')
                b.description = item.get('description')
                b.address = json.dumps(item.get('address')) if item.get('address') is not None else None
                b.renderer = json.dumps(item.get('renderer')) if item.get('renderer') is not None else None
                b.plan = json.dumps(item.get('plan')) if item.get('plan') is not None else None
                b.subway = json.dumps(item.get('subway')) if item.get('subway') is not None else None
                b.geometry_type = item.get('geometry', {}).get('type')
                b.geometry_coordinates = json.dumps(item.get('geometry', {}).get('coordinates')) if item.get('geometry', {}).get('coordinates') is not None else None
            else:
                # Создаем новую запись
                db.session.add(TrendBlock(
                    id=item['_id'],
                    name=item.get('name'),
                    crm_id=item.get('crm_id'),
                    district=item.get('district'),
                    description=item.get('description'),
                    address=json.dumps(item.get('address')) if item.get('address') is not None else None,
                    renderer=json.dumps(item.get('renderer')) if item.get('renderer') is not None else None,
                    plan=json.dumps(item.get('plan')) if item.get('plan') is not None else None,
                    subway=json.dumps(item.get('subway')) if item.get('subway') is not None else None,
                    geometry_type=item.get('geometry', {}).get('type'),
                    geometry_coordinates=json.dumps(item.get('geometry', {}).get('coordinates')) if item.get('geometry', {}).get('coordinates') is not None else None
                ))
    # Импорт buildings.json (без удаления, с обновлением)
    with open('trendagent/krd/buildings.json', encoding='utf-8') as f:
        for item in json.load(f):
            b = TrendBuilding.query.get(item['_id'])
            if b:
                b.crm_id = str(item.get('crm_id')) if item.get('crm_id') is not None else None
                b.name = item.get('name')
                b.block_id = item.get('block_id')
                b.building_type = item.get('building_type')
                b.queue = item.get('queue')
                b.subsidy = bool(item.get('subsidy')) if item.get('subsidy') is not None else None
                b.deadline = item.get('deadline')
                b.deadline_key = item.get('deadline_key')
                b.address_street = item.get('address', {}).get('street')
                b.address_house = item.get('address', {}).get('house')
                b.address_housing = item.get('address', {}).get('housing')
                b.address_street_en = item.get('address', {}).get('street_en')
                b.address_house_en = item.get('address', {}).get('house_en')
                b.address_housing_en = item.get('address', {}).get('housing_en')
                b.geometry_type = item.get('geometry', {}).get('type')
                b.geometry_coordinates = json.dumps(item.get('geometry', {}).get('coordinates')) if item.get('geometry', {}).get('coordinates') is not None else None
                # address_id не трогаем!
            else:
                db.session.add(TrendBuilding(
                    id=item['_id'],
                    crm_id=str(item.get('crm_id')) if item.get('crm_id') is not None else None,
                    name=item.get('name'),
                    block_id=item.get('block_id'),
                    building_type=item.get('building_type'),
                    queue=item.get('queue'),
                    subsidy=bool(item.get('subsidy')) if item.get('subsidy') is not None else None,
                    deadline=item.get('deadline'),
                    deadline_key=item.get('deadline_key'),
                    address_street=item.get('address', {}).get('street'),
                    address_house=item.get('address', {}).get('house'),
                    address_housing=item.get('address', {}).get('housing'),
                    address_street_en=item.get('address', {}).get('street_en'),
                    address_house_en=item.get('address', {}).get('house_en'),
                    address_housing_en=item.get('address', {}).get('housing_en'),
                    geometry_type=item.get('geometry', {}).get('type'),
                    geometry_coordinates=json.dumps(item.get('geometry', {}).get('coordinates')) if item.get('geometry', {}).get('coordinates') is not None else None
                    # address_id не задаём
                ))
    # Импорт apartments.json (без удаления, с обновлением)
    with open('trendagent/krd/apartments.json', encoding='utf-8') as f:
        for item in json.load(f):
            a = TrendApartment.query.get(item['_id'])
            if a:
                # Обновляем существующую запись
                a.area_balconies_total = item.get('area_balconies_total')
                a.area_given = item.get('area_given')
                a.area_kitchen = item.get('area_kitchen')
                a.area_rooms = item.get('area_rooms')
                a.area_rooms_total = item.get('area_rooms_total')
                a.area_total = item.get('area_total')
                a.block_address = item.get('block_address')
                a.block_builder = item.get('block_builder')
                a.block_builder_name = item.get('block_builder_name')
                a.block_city = item.get('block_city')
                a.block_crm_id = str(item.get('block_crm_id')) if item.get('block_crm_id') is not None else None
                a.block_district = item.get('block_district')
                a.block_district_name = item.get('block_district_name')
                a.block_geometry_type = item.get('block_geometry', {}).get('type')
                a.block_geometry_coordinates = json.dumps(item.get('block_geometry', {}).get('coordinates')) if item.get('block_geometry', {}).get('coordinates') is not None else None
                a.block_id = item.get('block_id')
                a.block_iscity = bool(item.get('block_iscity')) if item.get('block_iscity') is not None else None
                a.block_name = item.get('block_name')
                a.block_renderer = json.dumps(item.get('block_renderer')) if item.get('block_renderer') is not None else None
                a.block_subway = json.dumps(item.get('block_subway')) if item.get('block_subway') is not None else None
                a.block_subway_name = json.dumps(item.get('block_subway_name')) if item.get('block_subway_name') is not None else None
                a.building_bank = json.dumps(item.get('building_bank')) if item.get('building_bank') is not None else None
                a.building_contract = json.dumps(item.get('building_contract')) if item.get('building_contract') is not None else None
                a.building_deadline = item.get('building_deadline')
                a.building_id = item.get('building_id')
                a.building_installment = bool(item.get('building_installment')) if item.get('building_installment') is not None else None
                a.building_mortgage = bool(item.get('building_mortgage')) if item.get('building_mortgage') is not None else None
                a.building_name = item.get('building_name')
                a.building_queue = item.get('building_queue')
                a.building_subsidy = bool(item.get('building_subsidy')) if item.get('building_subsidy') is not None else None
                a.building_type = item.get('building_type')
                a.building_voen_mortgage = bool(item.get('building_voen_mortgage')) if item.get('building_voen_mortgage') is not None else None
                a.finishing = item.get('finishing')
                a.floor = item.get('floor')
                a.floors = item.get('floors')
                a.height = item.get('height')
                a.number = item.get('number')
                a.plan = json.dumps(item.get('plan')) if item.get('plan') is not None else None
                a.price = item.get('price')
                a.room = item.get('room')
                a.wc_count = item.get('wc_count')
            else:
                # Создаем новую запись
                db.session.add(TrendApartment(
                id=item['_id'],
                area_balconies_total=item.get('area_balconies_total'),
                area_given=item.get('area_given'),
                area_kitchen=item.get('area_kitchen'),
                area_rooms=item.get('area_rooms'),
                area_rooms_total=item.get('area_rooms_total'),
                area_total=item.get('area_total'),
                block_address=item.get('block_address'),
                block_builder=item.get('block_builder'),
                block_builder_name=item.get('block_builder_name'),
                block_city=item.get('block_city'),
                block_crm_id=str(item.get('block_crm_id')) if item.get('block_crm_id') is not None else None,
                block_district=item.get('block_district'),
                block_district_name=item.get('block_district_name'),
                block_geometry_type=item.get('block_geometry', {}).get('type'),
                block_geometry_coordinates=json.dumps(item.get('block_geometry', {}).get('coordinates')) if item.get('block_geometry', {}).get('coordinates') is not None else None,
                block_id=item.get('block_id'),
                block_iscity=bool(item.get('block_iscity')) if item.get('block_iscity') is not None else None,
                block_name=item.get('block_name'),
                block_renderer=json.dumps(item.get('block_renderer')) if item.get('block_renderer') is not None else None,
                block_subway=json.dumps(item.get('block_subway')) if item.get('block_subway') is not None else None,
                block_subway_name=json.dumps(item.get('block_subway_name')) if item.get('block_subway_name') is not None else None,
                building_bank=json.dumps(item.get('building_bank')) if item.get('building_bank') is not None else None,
                building_contract=json.dumps(item.get('building_contract')) if item.get('building_contract') is not None else None,
                building_deadline=item.get('building_deadline'),
                building_id=item.get('building_id'),
                building_installment=bool(item.get('building_installment')) if item.get('building_installment') is not None else None,
                building_mortgage=bool(item.get('building_mortgage')) if item.get('building_mortgage') is not None else None,
                building_name=item.get('building_name'),
                building_queue=item.get('building_queue'),
                building_subsidy=bool(item.get('building_subsidy')) if item.get('building_subsidy') is not None else None,
                building_type=item.get('building_type'),
                building_voen_mortgage=bool(item.get('building_voen_mortgage')) if item.get('building_voen_mortgage') is not None else None,
                finishing=item.get('finishing'),
                floor=item.get('floor'),
                floors=item.get('floors'),
                height=item.get('height'),
                number=item.get('number'),
                plan=json.dumps(item.get('plan')) if item.get('plan') is not None else None,
                price=item.get('price'),
                room=item.get('room'),
                wc_count=item.get('wc_count')
            ))
    db.session.commit()

@app.route('/api/import-trendagent', methods=['POST'])
def api_import_trendagent():
    try:
        import_trendagent_jsons()
        return jsonify({'success': True, 'message': 'Импорт завершен'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/trend-buildings')
def trend_buildings_page():
    return render_template('trend_buildings.html')

@app.route('/api/trend-buildings')
def api_trend_buildings():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '', type=str)
    query = TrendBuilding.query
    if search:
        query = query.filter(
            TrendBuilding.name.ilike(f'%{search}%') |
            TrendBuilding.address_street.ilike(f'%{search}%')
        )
    pagination = query.order_by(TrendBuilding.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for b in pagination.items:
        items.append({
            'id': b.id,
            'crm_id': b.crm_id,
            'name': b.name,
            'block_id': b.block_id,
            'building_type': b.building_type,
            'queue': b.queue,
            'subsidy': b.subsidy,
            'deadline': b.deadline,
            'deadline_key': b.deadline_key,
            'address_street': b.address_street,
            'address_house': b.address_house,
            'address_housing': b.address_housing,
            'address_street_en': b.address_street_en,
            'address_house_en': b.address_house_en,
            'address_housing_en': b.address_housing_en,
            'geometry_type': b.geometry_type,
            'geometry_coordinates': b.geometry_coordinates,
            'address_id': b.address_id,
            'dadata_address': {
                'id': b.dadata_address.id,
                'address': b.dadata_address.dadata_address,
                'full_address': b.dadata_address.dadata_full_address,
                'city': b.dadata_address.city,
                'street': b.dadata_address.street,
                'house': b.dadata_address.house
            } if b.dadata_address else None
        })
    return jsonify({
        'items': items,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })

def get_polygon_centroid(coords):
    # coords: [[[lon, lat], ...]]
    points = coords[0]
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    centroid_x = sum(x) / len(x)
    centroid_y = sum(y) / len(y)
    return centroid_x, centroid_y

@app.route('/api/geocode-trend-building/<string:building_id>', methods=['POST'])
def geocode_trend_building(building_id):
    import json
    b = TrendBuilding.query.get(building_id)
    if not b:
        return jsonify({'success': False, 'error': 'Здание не найдено'})
    if not b.geometry_coordinates:
        return jsonify({'success': False, 'error': 'Нет координат'})
    try:
        coords = json.loads(b.geometry_coordinates)
        lon, lat = get_polygon_centroid(coords)
        address = get_or_create_address(lat, lon)
        if not address:
            return jsonify({'success': False, 'error': 'Не удалось получить адрес'})
        b.address_id = address.id
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


@app.route('/api/geocode-all-trend-buildings', methods=['POST'])
def geocode_all_trend_buildings():
    """API endpoint для массового геокодирования всех зданий TrendAgent"""
    try:
        # Получаем все здания, у которых есть координаты, но нет адреса
        buildings = TrendBuilding.query.filter(
            TrendBuilding.geometry_coordinates.isnot(None),
            TrendBuilding.address_id.is_(None)
        ).all()
        
        processed = 0
        errors = 0
        
        for b in buildings:
            try:
                import json
                coords = json.loads(b.geometry_coordinates)
                lon, lat = get_polygon_centroid(coords)
                address = get_or_create_address(lat, lon)
                if address:
                    b.address_id = address.id
                    processed += 1
                else:
                    errors += 1
            except Exception as e:
                print(f"Ошибка при геокодировании здания {b.id}: {e}")
                errors += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'processed': processed,
            'errors': errors,
            'total': len(buildings)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/properties-fast')
def get_properties_fast():
    """Оптимизированная версия API для быстрой загрузки объектов недвижимости"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    property_id = request.args.get('id', type=int)
    contacts_only = request.args.get('contacts_only', type=int)
    in_complex_only = request.args.get('in_complex_only', type=int)
    in_sale_only = request.args.get('in_sale_only', type=int)
    
    # Если запрошен конкретный объект по ID - используем старый API
    if property_id:
        return get_properties()
    
    # Базовый запрос с предварительной загрузкой связанных данных
    query = Property.query.options(
        db.joinedload(Property.dadata_address),
        db.joinedload(Property.antiznak_status),
        db.joinedload(Property.rating_obj),
        db.joinedload(Property.yandex_rating_obj),
        db.joinedload(Property.yandex_link),
        db.joinedload(Property.generated_description_obj)
    )
    
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
    q = request.args.get('q', '').strip()
    
    # Применяем фильтры
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
    if in_sale_only:
        # Фильтруем объекты, которые есть в продаже
        utm_terms = db.session.query(SellerContact.utm_term)\
            .filter(SellerContact.utm_term.isnot(None))\
            .filter(SellerContact.utm_term != '')\
            .all()
        
        property_ids = []
        for (utm_term,) in utm_terms:
            try:
                property_ids.append(int(utm_term))
            except (ValueError, TypeError):
                continue
        
        if property_ids:
            query = query.filter(Property.id.in_(property_ids))
        else:
            query = query.filter(Property.id == -1)
    if yandex_complex:
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
    
    # Поиск
    if q:
        if q.isdigit():
            query = query.filter(
                db.or_(
                    Property.id == int(q),
                    Property.address.ilike(f'%{q}%'),
                    Property.contacts.ilike(f'%{q}%'),
                    PropertyYandexLink.yandex_complex_name.ilike(f'%{q}%')
                )
            )
        else:
            query = query.filter(
                db.or_(
                    Property.address.ilike(f'%{q}%'),
                    Property.contacts.ilike(f'%{q}%'),
                    PropertyYandexLink.yandex_complex_name.ilike(f'%{q}%')
                )
            )
    
    # Сортировка и пагинация
    pagination = query.order_by(Property.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Получаем все ID объектов для массовых запросов
    property_ids = [prop.id for prop in pagination.items]
    
    # Массовые запросы для связанных данных
    # 1. Получаем все телефоны, отправленные в КЦ
    sent_phones = set()
    if property_ids:
        phone_query = db.session.query(Lead2CallLog.phone).filter(
            Lead2CallLog.status == 'success'
        ).all()
        sent_phones = {phone[0] for phone in phone_query}
    
    # 2. Получаем все объекты в продаже
    in_sale_ids = set()
    if property_ids:
        sale_query = db.session.query(SellerContact.utm_term).filter(
            SellerContact.utm_term.in_([str(pid) for pid in property_ids])
        ).all()
        in_sale_ids = {int(utm[0]) for utm in sale_query if utm[0].isdigit()}
    
    # Формируем ответ
    properties = []
    for prop in pagination.items:
        sent_to_callcenter = False
        if prop.contacts:
            import re
            phone_match = re.search(r'(\+?\d{10,15})', prop.contacts)
            if phone_match:
                phone = phone_match.group(1)
                sent_to_callcenter = phone in sent_phones
        in_sale = prop.id in in_sale_ids
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
        antiznak_photos = []
        if prop.antiznak_status and prop.antiznak_status.photos:
            try:
                photos = json.loads(prop.antiznak_status.photos)
                antiznak_photos = [p.replace('\\', '/').replace('\\', '/') for p in photos]
            except Exception:
                pass
        # --- Новый блок для получения названия ЖК из yandex_newbuildings ---
        yandex_complex_name = None
        if prop.yandex_link and prop.yandex_link.yandex_building:
            yandex_complex_name = prop.yandex_link.yandex_building.complex_name
        elif prop.yandex_link:
            yandex_complex_name = prop.yandex_link.yandex_complex_name
        # ---
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
            'antiznak_photos': antiznak_photos,
            'antiznak_status_status': getattr(prop.antiznak_status, 'status', None) if prop.antiznak_status else None,
            'source_url': prop.source_url,
            'sent_to_callcenter': sent_to_callcenter,
            'rating': prop.rating_obj.rating if prop.rating_obj else None,
            'yandex_rating': prop.yandex_rating_obj.yandex_rating if prop.yandex_rating_obj else None,
            'yandex_complex_name': yandex_complex_name,
            'in_sale': in_sale,
            'generated_description': prop.generated_description_obj.generated_description if prop.generated_description_obj else None
        })
    
    return jsonify({
        'properties': properties,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


@app.route('/api/complex-photos/<int:address_id>')
def get_complex_photos(address_id):
    """Получить фотографии ЖК по адресу"""
    try:
        # Находим ЖК с этим адресом
        complex_obj = ResidentialComplex.query.filter_by(address_id=address_id).first()
        if not complex_obj:
            return jsonify({'photos': [], 'complex_name': None})
        
        # Получаем фотографии ЖК
        photos = ComplexPhoto.query.filter_by(complex_id=complex_obj.id).order_by(
            ComplexPhoto.is_main.desc(), ComplexPhoto.created_at.desc()
        ).all()
        
        photo_list = []
        for photo in photos:
            photo_list.append({
                'id': photo.id,
                'photo_path': photo.photo_path,
                'photo_url': photo.photo_url,
                'title': photo.title,
                'is_main': photo.is_main,
                'created_at': photo.created_at.isoformat() if photo.created_at else None
            })
        
        return jsonify({
            'photos': photo_list,
            'complex_name': complex_obj.name,
            'complex_id': complex_obj.id,
            'address': complex_obj.address
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/add-complex-photo', methods=['POST'])
def add_complex_photo():
    """Добавить фотографию к ЖК"""
    try:
        data = request.get_json()
        complex_id = data.get('complex_id')
        photo_path = data.get('photo_path')
        photo_url = data.get('photo_url')
        title = data.get('title', '')
        is_main = data.get('is_main', False)
        
        if not complex_id or not photo_path:
            return jsonify({'success': False, 'error': 'Не указан complex_id или photo_path'})
        
        # Если это главное фото, снимаем флаг с других
        if is_main:
            ComplexPhoto.query.filter_by(complex_id=complex_id, is_main=True).update({'is_main': False})
        
        photo = ComplexPhoto(
            complex_id=complex_id,
            photo_path=photo_path,
            photo_url=photo_url,
            title=title,
            is_main=is_main
        )
        db.session.add(photo)
        db.session.commit()
        
        return jsonify({'success': True, 'photo_id': photo.id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/add-complex-photos-from-folder', methods=['POST'])
def add_complex_photos_from_folder():
    """Добавить фотографии к ЖК из папки"""
    import os
    import glob
    
    try:
        data = request.get_json()
        complex_id = data.get('complex_id')
        photos_path = data.get('photos_path')
        photo_title = data.get('photo_title', '')
        is_main = data.get('is_main', False)
        
        if not complex_id or not photos_path:
            return jsonify({'success': False, 'error': 'Не указан complex_id или photos_path'})
        
        # Проверяем существование папки
        if not os.path.exists(photos_path):
            return jsonify({'success': False, 'error': f'Папка не найдена: {photos_path}'})
        
        # Ищем все изображения в папке
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.webp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(photos_path, ext)))
            image_files.extend(glob.glob(os.path.join(photos_path, ext.upper())))
        
        if not image_files:
            return jsonify({'success': False, 'error': f'В папке не найдены изображения: {photos_path}'})
        
        # Сортируем файлы по имени
        image_files.sort()
        
        # Если это главное фото, снимаем флаг с других
        if is_main:
            ComplexPhoto.query.filter_by(complex_id=complex_id, is_main=True).update({'is_main': False})
        
        added_photos = []
        for i, image_file in enumerate(image_files):
            # Создаем относительный путь для веб-доступа
            relative_path = os.path.relpath(image_file, os.getcwd())
            web_path = f'/{relative_path.replace(os.sep, "/")}'
            
            # Определяем, является ли это главным фото
            is_main_photo = is_main and i == 0
            
            photo = ComplexPhoto(
                complex_id=complex_id,
                photo_path=web_path,
                photo_url=web_path,
                title=f"{photo_title} - фото {i+1}" if photo_title else f"Фото {i+1}",
                is_main=is_main_photo
            )
            db.session.add(photo)
            added_photos.append({
                'id': photo.id,
                'path': web_path,
                'title': photo.title,
                'is_main': is_main_photo
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'added_count': len(added_photos),
            'photos': added_photos
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/export-properties-csv')
def export_properties_csv():
    """Экспорт объектов недвижимости в CSV"""
    try:
        print("🎯 Начинаем экспорт CSV")
        
        # Получаем все параметры фильтрации из запроса
        q = request.args.get('q', '').strip()
        contacts_only = request.args.get('contacts_only', '0') == '1'
        in_sale_only = request.args.get('in_sale_only', '0') == '1'
        yandex_complex = request.args.get('yandex_complex', '').strip()
        price_min = request.args.get('price_min', type=float)
        price_max = request.args.get('price_max', type=float)
        area_min = request.args.get('area_min', type=float)
        area_max = request.args.get('area_max', type=float)
        rooms = request.args.get('rooms', type=int)
        rating_min = request.args.get('rating_min', type=int)
        rating_max = request.args.get('rating_max', type=int)
        yandex_rating_min = request.args.get('yandex_rating_min', type=int)
        yandex_rating_max = request.args.get('yandex_rating_max', type=int)
        in_complex_only = request.args.get('in_complex_only', type=int)
        yandex_building_id = request.args.get('yandex_building_id', type=int)
        
        print(f"📝 Параметры фильтрации: q='{q}', contacts_only={contacts_only}, in_sale_only={in_sale_only}, yandex_complex='{yandex_complex}', price_min={price_min}, price_max={price_max}")
        
        # Упрощаем запрос - начинаем только с Property
        query = db.session.query(Property)
        
        # Добавляем JOIN с Address только если нужен
        if any([q, price_min is not None, price_max is not None, area_min is not None, area_max is not None, rooms is not None]):
            query = query.outerjoin(Address, Property.address_id == Address.id)
        
        # Добавляем JOIN с PropertyYandexLink только если нужен
        if any([yandex_complex, in_complex_only, yandex_building_id, yandex_rating_min is not None, yandex_rating_max is not None]):
            query = query.outerjoin(PropertyYandexLink, Property.id == PropertyYandexLink.property_id)
            if yandex_building_id:
                query = query.outerjoin(YandexNewBuilding, PropertyYandexLink.yandex_building_id == YandexNewBuilding.id)

        # Применяем фильтры
        if q:
            if q.isdigit():
                query = query.filter(
                    or_(
                        Property.id == int(q),
                        Property.address.ilike(f'%{q}%'),
                        Property.contacts.ilike(f'%{q}%')
                    )
                )
            else:
                query = query.filter(
                    or_(
                        Property.address.ilike(f'%{q}%'),
                        Property.contacts.ilike(f'%{q}%')
                    )
                )
        
        if contacts_only:
            query = query.filter(
                Property.contacts.isnot(None),
                Property.contacts != '',
                Property.contacts != 'nan',
                Property.contacts != 'None'
            )
        
        if in_sale_only:
            # Фильтруем объекты, которые есть в продаже
            utm_terms = db.session.query(SellerContact.utm_term)\
                .filter(SellerContact.utm_term.isnot(None))\
                .filter(SellerContact.utm_term != '')\
                .all()
            
            property_ids = []
            for (utm_term,) in utm_terms:
                try:
                    property_ids.append(int(utm_term))
                except (ValueError, TypeError):
                    continue
            
            if property_ids:
                query = query.filter(Property.id.in_(property_ids))
            else:
                query = query.filter(Property.id == -1)
        
        if yandex_complex:
            # Добавляем JOIN если его еще нет
            if not any([yandex_complex, in_complex_only, yandex_building_id, yandex_rating_min is not None, yandex_rating_max is not None]):
                query = query.outerjoin(PropertyYandexLink, Property.id == PropertyYandexLink.property_id)
            query = query.filter(PropertyYandexLink.yandex_complex_name.ilike(f'%{yandex_complex}%'))
        
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
        
        if in_complex_only:
            # Добавляем JOIN если его еще нет
            if not any([yandex_complex, in_complex_only, yandex_building_id, yandex_rating_min is not None, yandex_rating_max is not None]):
                query = query.outerjoin(PropertyYandexLink, Property.id == PropertyYandexLink.property_id)
            query = query.filter(PropertyYandexLink.property_id.isnot(None))
        
        if rating_min is not None or rating_max is not None:
            query = query.outerjoin(PropertyRating, Property.id == PropertyRating.property_id)
            if rating_min is not None:
                query = query.filter(PropertyRating.rating >= rating_min)
            if rating_max is not None:
                query = query.filter(PropertyRating.rating <= rating_max)
        
        if yandex_rating_min is not None or yandex_rating_max is not None:
            # Добавляем JOIN если его еще нет
            if not any([yandex_complex, in_complex_only, yandex_building_id, yandex_rating_min is not None, yandex_rating_max is not None]):
                query = query.outerjoin(PropertyYandexLink, Property.id == PropertyYandexLink.property_id)
            query = query.outerjoin(PropertyYandexRating, Property.id == PropertyYandexRating.property_id)
            if yandex_rating_min is not None:
                query = query.filter(PropertyYandexRating.yandex_rating >= yandex_rating_min)
            if yandex_rating_max is not None:
                query = query.filter(PropertyYandexRating.yandex_rating <= yandex_rating_max)
        
        if yandex_building_id:
            # Добавляем JOIN если его еще нет
            if not any([yandex_complex, in_complex_only, yandex_building_id, yandex_rating_min is not None, yandex_rating_max is not None]):
                query = query.outerjoin(PropertyYandexLink, Property.id == PropertyYandexLink.property_id)
            query = query.filter(PropertyYandexLink.yandex_building_id == yandex_building_id)
        
        # Проверяем, есть ли фильтры
        has_filters = bool(q or contacts_only or in_sale_only or yandex_complex or 
                          price_min is not None or price_max is not None or 
                          area_min is not None or area_max is not None or 
                          rooms is not None or rating_min is not None or 
                          rating_max is not None or yandex_rating_min is not None or 
                          yandex_rating_max is not None or in_complex_only)
        
        if not has_filters:
            print("⚠️ Нет фильтров - экспортируем все объекты")
        else:
            print(f"🔍 Экспортируем результаты поиска с фильтрами")
        
        properties = query.all()
        print(f"📊 Найдено объектов для экспорта: {len(properties)}")
        
        # Отладочная информация
        if len(properties) == 0:
            print("⚠️ ВНИМАНИЕ: Запрос вернул 0 объектов!")
            print(f"🔍 SQL запрос: {query}")
            # Попробуем простой запрос без фильтров
            simple_count = Property.query.count()
            print(f"📈 Всего объектов в базе: {simple_count}")
        
        # Создаем CSV в памяти
        output = StringIO()
        writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        
        # Заголовки
        headers = [
            'ID объекта',
            'Адрес из address_id',
            'Адрес (DaData)',
            'Жилой комплекс',
            'Цена',
            'Площадь',
            'Количество комнат',
            'Этаж',
            'Всего этажей',
            'Заголовок',
            'Описание',
            'Ссылка на фото',
            'Год постройки'
        ]
        writer.writerow(headers)
        
        # Данные
        for i, prop in enumerate(properties, 1):
            if i % 100 == 0:
                print(f"📝 Обработано объектов: {i}/{len(properties)}")
            
            # Получаем связанный адрес
            address = None
            if prop.address_id:
                address = Address.query.get(prop.address_id)
            
            # Получаем информацию о жилом комплексе
            yandex_complex_name = ""
            if prop and hasattr(prop, 'yandex_link') and prop.yandex_link:
                yandex_complex_name = prop.yandex_link.yandex_complex_name or ""
                if i <= 5:  # Отладочная информация для первых 5 объектов
                    print(f"🔍 Объект {prop.id}: yandex_link={prop.yandex_link}, yandex_complex_name='{yandex_complex_name}'")
            else:
                if i <= 5:  # Отладочная информация для первых 5 объектов
                    print(f"🔍 Объект {prop.id}: yandex_link отсутствует")
            
            photo_url = ""
            if prop and hasattr(prop, 'id') and prop.id:
                photo_files = []
                for complex_name in ['antiznak']:
                    photo_dir = os.path.join('photos', complex_name, str(prop.id))
                    if os.path.exists(photo_dir):
                        for file in os.listdir(photo_dir):
                            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                                photo_files.append(f'/photos/{complex_name}/{prop.id}/{file}')
                                break
                if photo_files:
                    photo_url = photo_files[0]
            
            dadata_address = ""
            if address and hasattr(address, 'dadata_address') and address.dadata_address:
                dadata_address = address.dadata_address
            
            generated_description = ""
            if prop and hasattr(prop, 'generated_description_obj') and prop.generated_description_obj:
                generated_description = prop.generated_description_obj.generated_description or ""
            
            description = generated_description or (getattr(prop, 'description', '') or "")
            
            row = [
                getattr(prop, 'id', '') if prop else '',
                getattr(address, 'address', '') if address else '',
                dadata_address,
                yandex_complex_name,
                getattr(prop, 'price', '') if prop else '',
                getattr(prop, 'total_area', '') if prop else '',
                getattr(prop, 'rooms_count', '') if prop else '',
                getattr(prop, 'floor', '') if prop else '',
                getattr(prop, 'total_floors', '') if prop else '',
                getattr(prop, 'title', '') if prop else '',
                description,
                photo_url,
                getattr(prop, 'construction_year', '') if prop else ''
            ]
            
            if not all([(str(x).strip() if x is not None else '') == '' for x in row]):
                writer.writerow(row)
                if i <= 5:  # Показываем первые 5 строк для отладки
                    print(f"📝 Строка {i}: {row}")
        
        print(f"✅ CSV создан, записей: {len(properties)}")
        
        # Подготавливаем файл для отправки
        output.seek(0)
        
        # Создаем временный файл
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig', newline='') as tmp_file:
            tmp_file.write(output.getvalue())
            tmp_file_path = tmp_file.name
        
        print(f"📁 Файл сохранен: {tmp_file_path}")
        
        return send_file(
            tmp_file_path,
            as_attachment=True,
            download_name=f'properties_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        import traceback
        print(f"❌ Ошибка экспорта в CSV: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


class PriceHistory(db.Model):
    """Таблица для отслеживания изменений цены объектов недвижимости"""
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    old_price = db.Column(db.Float)  # Старая цена
    new_price = db.Column(db.Float, nullable=False)  # Новая цена
    price_change = db.Column(db.Float)  # Разница в цене (new_price - old_price)
    change_percent = db.Column(db.Float)  # Процент изменения
    changed_by = db.Column(db.String(100), default="system")  # Кто изменил
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с объектом недвижимости
    property = db.relationship('Property', backref='price_history')


def log_price_change(property_id, old_price, new_price, changed_by="system"):
    """Логирует изменение цены объекта недвижимости"""
    try:
        if old_price is None:
            old_price = 0
        
        price_change = new_price - old_price if old_price else 0
        change_percent = ((new_price - old_price) / old_price * 100) if old_price and old_price > 0 else 0
        
        price_record = PriceHistory(
            property_id=property_id,
            old_price=old_price,
            new_price=new_price,
            price_change=price_change,
            change_percent=change_percent,
            changed_by=changed_by
        )
        db.session.add(price_record)
        db.session.commit()
        
        change_symbol = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"
        print(f"{change_symbol} Изменение цены объекта {property_id}: {old_price:,} → {new_price:,} ₽ ({change_percent:+.1f}%)")
    except Exception as e:
        print(f"❌ Ошибка при записи изменения цены: {e}")
        db.session.rollback()


def check_and_log_price_change(property_obj, old_price, changed_by="system"):
    """Проверяет и логирует изменение цены объекта"""
    if property_obj.price != old_price:
        log_price_change(property_obj.id, old_price, property_obj.price, changed_by)





@app.route('/api/price-history/<int:property_id>')
def get_price_history(property_id):
    """Получить историю изменений цены объекта недвижимости"""
    try:
        price_records = PriceHistory.query.filter_by(property_id=property_id)\
            .order_by(PriceHistory.changed_at.desc()).all()
        
        result = []
        for record in price_records:
            result.append({
                'id': record.id,
                'old_price': record.old_price,
                'new_price': record.new_price,
                'price_change': record.price_change,
                'change_percent': record.change_percent,
                'changed_by': record.changed_by,
                'changed_at': record.changed_at.isoformat() if record.changed_at else None
            })
        
        return jsonify({
            'success': True,
            'property_id': property_id,
            'price_history': result,
            'total_records': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/recent-price-changes')
def get_recent_price_changes():
    """Получить последние изменения цен по всем объектам"""
    try:
        limit = request.args.get('limit', 50, type=int)
        days = request.args.get('days', 7, type=int)
        
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        price_records = PriceHistory.query\
            .filter(PriceHistory.changed_at >= cutoff_date)\
            .order_by(PriceHistory.changed_at.desc())\
            .limit(limit).all()
        
        result = []
        for record in price_records:
            result.append({
                'id': record.id,
                'property_id': record.property_id,
                'old_price': record.old_price,
                'new_price': record.new_price,
                'price_change': record.price_change,
                'change_percent': record.change_percent,
                'changed_by': record.changed_by,
                'changed_at': record.changed_at.isoformat() if record.changed_at else None
            })
        
        return jsonify({
            'success': True,
            'price_changes': result,
            'total_records': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/price-statistics')
def get_price_statistics():
    """Получить статистику по изменениям цен"""
    try:
        days = request.args.get('days', 30, type=int)
        
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Общая статистика
        total_changes = PriceHistory.query.filter(PriceHistory.changed_at >= cutoff_date).count()
        price_increases = PriceHistory.query.filter(
            PriceHistory.changed_at >= cutoff_date,
            PriceHistory.price_change > 0
        ).count()
        price_decreases = PriceHistory.query.filter(
            PriceHistory.changed_at >= cutoff_date,
            PriceHistory.price_change < 0
        ).count()
        
        # Средние изменения
        avg_increase = db.session.query(db.func.avg(PriceHistory.change_percent))\
            .filter(PriceHistory.changed_at >= cutoff_date, PriceHistory.price_change > 0).scalar() or 0
        avg_decrease = db.session.query(db.func.avg(PriceHistory.change_percent))\
            .filter(PriceHistory.changed_at >= cutoff_date, PriceHistory.price_change < 0).scalar() or 0
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_changes': total_changes,
                'price_increases': price_increases,
                'price_decreases': price_decreases,
                'avg_increase_percent': round(avg_increase, 1),
                'avg_decrease_percent': round(avg_decrease, 1),
                'period_days': days
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/complex-properties/<complex_name>')
def get_complex_properties(complex_name):
    """Получить все квартиры конкретного жилого комплекса (по названию)"""
    import urllib.parse
    
    # Декодируем название комплекса из URL
    complex_name = urllib.parse.unquote(complex_name)
    
    # Получаем информацию о ЖК из Яндекс-новостроек
    yandex_complex = YandexNewBuilding.query.filter_by(complex_name=complex_name).first()
    
    # Получаем квартиры для данного ЖК с загрузкой связанных данных
    query = Property.query.join(PropertyYandexLink).options(
        db.joinedload(Property.rating_obj),
        db.joinedload(Property.dadata_address)
    ).filter(
        PropertyYandexLink.yandex_complex_name == complex_name
    )
    
    properties = query.all()
    
    # Подсчитываем статистику
    total_properties = len(properties)
    avg_price = sum(p.price for p in properties) / total_properties if total_properties > 0 else 0
    min_price = min(p.price for p in properties) if total_properties > 0 else 0
    max_price = max(p.price for p in properties) if total_properties > 0 else 0
    
    # Формируем ответ с квартирами
    properties_data = []
    for prop in properties:
        # Получаем первое изображение
        first_image = None
        if prop.images:
            images_list = prop.images.split(',')
            if images_list:
                first_image = images_list[0].strip()
        
        properties_data.append({
            'id': prop.id,
            'title': prop.title or 'Без названия',
            'address': prop.address or 'Адрес не указан',
            'price': prop.price,
            'total_area': prop.total_area,
            'rooms_count': prop.rooms_count,
            'floor': prop.floor,
            'total_floors': prop.total_floors,
            'construction_year': prop.construction_year,
            'image': first_image,
            'longitude': prop.longitude,
            'latitude': prop.latitude,
            'rating': prop.rating_obj.rating if getattr(prop, 'rating_obj', None) else None
        })
    
    # Формируем статистику
    statistics = {
        'total_properties': total_properties,
        'avg_price': avg_price,
        'min_price': min_price,
        'max_price': max_price
    }
    
    return jsonify({
        'complex_name': complex_name,
        'address': yandex_complex.address if yandex_complex else None,
        'properties': properties_data,
        'statistics': statistics,
        'avg_price': avg_price,
        'rating': None  # Можно добавить рейтинг ЖК, если есть
    })


@app.route('/api/property/<int:property_id>/complex')
def get_property_complex(property_id):
    """Получить ЖК по ID объекта недвижимости"""
    # Получаем объект недвижимости с его связью с ЖК
    property_item = Property.query.options(
        db.joinedload(Property.yandex_link)
    ).get(property_id)
    
    if not property_item:
        return jsonify({'error': 'Объект не найден'}), 404
    
    # Проверяем, есть ли связь с ЖК
    if not property_item.yandex_link or not property_item.yandex_link.yandex_complex_name:
        return jsonify({'error': 'ЖК не найден для данного объекта'}), 404
    
    complex_name = property_item.yandex_link.yandex_complex_name
    slug = property_item.yandex_link.slug
    
    # Получаем информацию о ЖК из Яндекс-новостроек
    yandex_complex = YandexNewBuilding.query.filter_by(complex_name=complex_name).first()
    
    # Получаем все квартиры для данного ЖК
    query = Property.query.join(PropertyYandexLink).options(
        db.joinedload(Property.rating_obj),
        db.joinedload(Property.dadata_address)
    ).filter(
        PropertyYandexLink.yandex_complex_name == complex_name
    )
    
    properties = query.all()
    
    # Подсчитываем статистику
    total_properties = len(properties)
    avg_price = sum(p.price for p in properties) / total_properties if total_properties > 0 else 0
    min_price = min(p.price for p in properties) if total_properties > 0 else 0
    max_price = max(p.price for p in properties) if total_properties > 0 else 0
    
    # Формируем ответ с квартирами
    properties_data = []
    for prop in properties:
        # Получаем первое изображение
        first_image = None
        if prop.images:
            images_list = prop.images.split(',')
            if images_list:
                first_image = images_list[0].strip()
        
        properties_data.append({
            'id': prop.id,
            'title': prop.title or 'Без названия',
            'address': prop.address or 'Адрес не указан',
            'price': prop.price,
            'total_area': prop.total_area,
            'rooms_count': prop.rooms_count,
            'floor': prop.floor,
            'total_floors': prop.total_floors,
            'construction_year': prop.construction_year,
            'image': first_image,
            'longitude': prop.longitude,
            'latitude': prop.latitude,
            'rating': prop.rating_obj.rating if getattr(prop, 'rating_obj', None) else None
        })
    
    # Формируем статистику
    statistics = {
        'total_properties': total_properties,
        'avg_price': avg_price,
        'min_price': min_price,
        'max_price': max_price
    }
    
    return jsonify({
        'complex_name': complex_name,
        'slug': slug,
        'address': yandex_complex.address if yandex_complex else None,
        'properties': properties_data,
        'statistics': statistics,
        'avg_price': avg_price,
        'rating': None  # Можно добавить рейтинг ЖК, если есть
    })


@app.route('/api/complex-properties-slug/<slug>')
def get_complex_properties_by_slug(slug):
    """Получить все квартиры конкретного жилого комплекса (по slug из таблицы связей)"""
    import urllib.parse
    
    # Декодируем slug из URL
    slug = urllib.parse.unquote(slug)
    
    # Получаем первую связь с этим slug для получения complex_name
    link = PropertyYandexLink.query.filter_by(slug=slug).first()
    
    if not link:
        return jsonify({'error': 'ЖК не найден'}), 404
    
    complex_name = link.yandex_complex_name
    
    # Получаем все квартиры для данного ЖК
    query = Property.query.join(PropertyYandexLink).options(
        db.joinedload(Property.rating_obj),
        db.joinedload(Property.dadata_address)
    ).filter(
        PropertyYandexLink.yandex_complex_name == complex_name
    )
    
    properties = query.all()
    
    # Подсчитываем статистику
    total_properties = len(properties)
    avg_price = sum(p.price for p in properties) / total_properties if total_properties > 0 else 0
    min_price = min(p.price for p in properties) if total_properties > 0 else 0
    max_price = max(p.price for p in properties) if total_properties > 0 else 0
    
    # Формируем ответ с квартирами
    properties_data = []
    for prop in properties:
        # Получаем первое изображение
        first_image = None
        if prop.images:
            images_list = prop.images.split(',')
            if images_list:
                first_image = images_list[0].strip()
        
        properties_data.append({
            'id': prop.id,
            'title': prop.title or 'Без названия',
            'address': prop.address or 'Адрес не указан',
            'price': prop.price,
            'total_area': prop.total_area,
            'rooms_count': prop.rooms_count,
            'floor': prop.floor,
            'total_floors': prop.total_floors,
            'construction_year': prop.construction_year,
            'image': first_image,
            'longitude': prop.longitude,
            'latitude': prop.latitude,
            'rating': prop.rating_obj.rating if getattr(prop, 'rating_obj', None) else None
        })
    
    # Формируем статистику
    statistics = {
        'total_properties': total_properties,
        'avg_price': avg_price,
        'min_price': min_price,
        'max_price': max_price
    }
    
    # Получаем информацию о ЖК из Яндекс-новостроек
    yandex_complex = YandexNewBuilding.query.filter_by(complex_name=complex_name).first()
    
    return jsonify({
        'complex_name': complex_name,
        'slug': slug,
        'address': yandex_complex.address if yandex_complex else None,
        'properties': properties_data,
        'statistics': statistics,
        'avg_price': avg_price,
        'rating': None  # Можно добавить рейтинг ЖК, если есть
    })


@app.route('/api/complex-info/<complex_name>')
def get_complex_info(complex_name):
    """Получить информацию о конкретном жилом комплексе"""
    # Декодируем название комплекса из URL
    import urllib.parse
    complex_name = urllib.parse.unquote(complex_name)
    
    # Получаем информацию о ЖК из Яндекс-новостроек
    yandex_complex = YandexNewBuilding.query.filter_by(complex_name=complex_name).first()
    
    # Получаем статистику по квартирам
    properties_query = Property.query.join(PropertyYandexLink).filter(
        PropertyYandexLink.yandex_complex_name == complex_name
    )
    
    total_properties = properties_query.count()
    
    # Статистика по комнатам
    rooms_stats = db.session.query(
        Property.rooms_count,
        db.func.count(Property.id).label('count'),
        db.func.avg(Property.price).label('avg_price'),
        db.func.min(Property.price).label('min_price'),
        db.func.max(Property.price).label('max_price')
    ).join(PropertyYandexLink).filter(
        PropertyYandexLink.yandex_complex_name == complex_name,
        Property.rooms_count.isnot(None)
    ).group_by(Property.rooms_count).all()
    
    # Статистика по цене
    price_stats = db.session.query(
        db.func.avg(Property.price).label('avg_price'),
        db.func.min(Property.price).label('min_price'),
        db.func.max(Property.price).label('max_price'),
        db.func.avg(Property.price_per_sqm).label('avg_price_per_sqm')
    ).join(PropertyYandexLink).filter(
        PropertyYandexLink.yandex_complex_name == complex_name,
        Property.price.isnot(None)
    ).first()
    
    # Получаем фотографии ЖК
    complex_photos = []
    if yandex_complex and yandex_complex.address_id:
        # Ищем ЖК с фотографиями по адресу
        complex_obj = ResidentialComplex.query.filter_by(address_id=yandex_complex.address_id).first()
        if complex_obj and complex_obj.photo_url:
            complex_photos.append({
                'id': complex_obj.id,
                'photo_path': complex_obj.photo_url,
                'photo_url': complex_obj.photo_url,
                'title': f'Фото ЖК {complex_obj.name}',
                'is_main': True
            })
    
    return jsonify({
        'complex_name': complex_name,
        'yandex_info': {
            'id': yandex_complex.id if yandex_complex else None,
            'region': yandex_complex.region if yandex_complex else None,
            'complex_id': yandex_complex.complex_id if yandex_complex else None,
            'queue': yandex_complex.queue if yandex_complex else None,
            'ready_date': yandex_complex.ready_date if yandex_complex else None,
            'address': yandex_complex.address if yandex_complex else None,
            'url': yandex_complex.url if yandex_complex else None,
            'dadata_address': yandex_complex.dadata_address.dadata_address if yandex_complex and yandex_complex.dadata_address else None
        },
        'statistics': {
            'total_properties': total_properties,
            'rooms_stats': [
                {
                    'rooms_count': stat.rooms_count,
                    'count': stat.count,
                    'avg_price': float(stat.avg_price) if stat.avg_price else None,
                    'min_price': float(stat.min_price) if stat.min_price else None,
                    'max_price': float(stat.max_price) if stat.max_price else None
                }
                for stat in rooms_stats
            ],
            'price_stats': {
                'avg_price': float(price_stats.avg_price) if price_stats and price_stats.avg_price else None,
                'min_price': float(price_stats.min_price) if price_stats and price_stats.min_price else None,
                'max_price': float(price_stats.max_price) if price_stats and price_stats.max_price else None,
                'avg_price_per_sqm': float(price_stats.avg_price_per_sqm) if price_stats and price_stats.avg_price_per_sqm else None
            }
        },
        'photos': complex_photos
    })


@app.route('/api/complexes-with-properties')
def get_complexes_with_properties():
    """Получить все жилые комплексы с их квартирами"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '', type=str)
    region = request.args.get('region', '', type=str)
    
    # Получаем все уникальные названия ЖК из связей
    query = db.session.query(PropertyYandexLink.yandex_complex_name).distinct()
    
    if search:
        query = query.filter(PropertyYandexLink.yandex_complex_name.ilike(f'%{search}%'))
    
    # Получаем общее количество ЖК
    total_complexes = query.count()
    pages = (total_complexes + per_page - 1) // per_page
    
    # Применяем пагинацию
    complex_names = query.offset((page - 1) * per_page).limit(per_page).all()
    
    complexes_data = []
    
    for (complex_name,) in complex_names:
        if not complex_name:
            continue
            
        # Получаем информацию о ЖК из Яндекс-новостроек
        yandex_complex = YandexNewBuilding.query.filter_by(complex_name=complex_name).first()
        
        # Получаем квартиры для данного ЖК (ограничиваем количество для производительности)
        properties_query = Property.query.join(PropertyYandexLink).filter(
            PropertyYandexLink.yandex_complex_name == complex_name
        )
        
        total_properties = properties_query.count()
        
        # Получаем только первые 10 квартир для предварительного просмотра
        properties = properties_query.limit(10).all()
        
        # Статистика по комнатам
        rooms_stats = db.session.query(
            Property.rooms_count,
            db.func.count(Property.id).label('count'),
            db.func.avg(Property.price).label('avg_price'),
            db.func.min(Property.price).label('min_price'),
            db.func.max(Property.price).label('max_price')
        ).join(PropertyYandexLink).filter(
            PropertyYandexLink.yandex_complex_name == complex_name,
            Property.rooms_count.isnot(None)
        ).group_by(Property.rooms_count).all()
        
        # Статистика по цене
        price_stats = db.session.query(
            db.func.avg(Property.price).label('avg_price'),
            db.func.min(Property.price).label('min_price'),
            db.func.max(Property.price).label('max_price'),
            db.func.avg(Property.price_per_sqm).label('avg_price_per_sqm')
        ).join(PropertyYandexLink).filter(
            PropertyYandexLink.yandex_complex_name == complex_name,
            Property.price.isnot(None)
        ).first()
        
        # Получаем фотографии ЖК
        complex_photos = []
        if yandex_complex and yandex_complex.address_id:
            complex_obj = ResidentialComplex.query.filter_by(address_id=yandex_complex.address_id).first()
            if complex_obj and complex_obj.photo_url:
                complex_photos.append({
                    'id': complex_obj.id,
                    'photo_path': complex_obj.photo_url,
                    'photo_url': complex_obj.photo_url,
                    'title': f'Фото ЖК {complex_obj.name}',
                    'is_main': True
                })
        
        # Формируем данные квартир
        properties_data = []
        for prop in properties:
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
            
            properties_data.append({
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
                                    json.loads(prop.antiznak_status.photos)] if getattr(prop, 'antiznak_status', None) and prop.antiznak_status.photos else [],
                'antiznak_status_status': getattr(prop.antiznak_status, 'status', None),
                'source_url': prop.source_url,
                'sent_to_callcenter': sent_to_callcenter,
                'rating': prop.rating_obj.rating if getattr(prop, 'rating_obj', None) else None,
                'yandex_rating': prop.yandex_rating_obj.yandex_rating if getattr(prop, 'yandex_rating_obj', None) else None,
                'generated_description': prop.generated_description_obj.generated_description if getattr(prop, 'generated_description_obj', None) else None
            })
        
        complexes_data.append({
            'complex_name': complex_name,
            'yandex_info': {
                'id': yandex_complex.id if yandex_complex else None,
                'region': yandex_complex.region if yandex_complex else None,
                'complex_id': yandex_complex.complex_id if yandex_complex else None,
                'queue': yandex_complex.queue if yandex_complex else None,
                'ready_date': yandex_complex.ready_date if yandex_complex else None,
                'address': yandex_complex.address if yandex_complex else None,
                'url': yandex_complex.url if yandex_complex else None,
                'dadata_address': yandex_complex.dadata_address.dadata_address if yandex_complex and yandex_complex.dadata_address else None
            },
            'statistics': {
                'total_properties': total_properties,
                'rooms_stats': [
                    {
                        'rooms_count': stat.rooms_count,
                        'count': stat.count,
                        'avg_price': float(stat.avg_price) if stat.avg_price else None,
                        'min_price': float(stat.min_price) if stat.min_price else None,
                        'max_price': float(stat.max_price) if stat.max_price else None
                    }
                    for stat in rooms_stats
                ],
                'price_stats': {
                    'avg_price': float(price_stats.avg_price) if price_stats and price_stats.avg_price else None,
                    'min_price': float(price_stats.min_price) if price_stats and price_stats.min_price else None,
                    'max_price': float(price_stats.max_price) if price_stats and price_stats.max_price else None,
                    'avg_price_per_sqm': float(price_stats.avg_price_per_sqm) if price_stats and price_stats.avg_price_per_sqm else None
                }
            },
            'photos': complex_photos,
            'properties': properties_data
        })
    
    return jsonify({
        'complexes': complexes_data,
        'total': total_complexes,
        'pages': pages,
        'current_page': page,
        'per_page': per_page
    })


@app.route('/api-docs')
def api_docs():
    return render_template('api-docs.html')


@app.route('/api/properties-light')
def get_properties_light():
    """Легковесный API для быстрой загрузки списка объектов недвижимости"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 48, type=int)  # Размер страницы по умолчанию
    property_id = request.args.get('id', type=int)
    
    # Если запрошен конкретный объект по ID - используем полный API
    if property_id:
        return get_properties()
    
    # Базовый запрос с загрузкой связанных данных и фильтрацией некорректных данных
    query = Property.query.options(
        db.joinedload(Property.rating_obj),
        db.joinedload(Property.dadata_address)
    ).filter(
        Property.id > 0,
        Property.title != 'nan',
        Property.title != '',
        Property.address != 'nan',
        Property.address != ''
    )
    
    # Фильтры
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    area_min = request.args.get('area_min', type=float)
    area_max = request.args.get('area_max', type=float)
    rooms = request.args.get('rooms', type=int)
    address = request.args.get('address', '')
    q = request.args.get('q', '').strip()
    
    # Применяем фильтры
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
    
    # Поиск
    if q:
        if q.isdigit():
            query = query.filter(
                db.or_(
                    Property.id == int(q),
                    Property.address.ilike(f'%{q}%')
                )
            )
        else:
            query = query.filter(Property.address.ilike(f'%{q}%'))
    
    # Сортировка и пагинация
    pagination = query.order_by(Property.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Формируем легковесный ответ
    properties = []
    for prop in pagination.items:
        # Получаем первое изображение
        first_image = None
        if prop.images:
            images_list = prop.images.split(',')
            if images_list:
                first_image = images_list[0].strip()
        
        # Получаем рейтинг из связанной таблицы
        rating = None
        if hasattr(prop, 'rating_obj') and prop.rating_obj:
            rating = prop.rating_obj.rating
        
        # Получаем информацию об адресе из связанной таблицы
        dadata_address = None
        if prop.dadata_address:
            dadata_address = {
                'id': prop.dadata_address.id,
                'address': prop.dadata_address.dadata_address,
                'full_address': prop.dadata_address.dadata_full_address,
                'city': prop.dadata_address.city,
                'street': prop.dadata_address.street,
                'house': prop.dadata_address.house,
                'latitude': prop.dadata_address.latitude,
                'longitude': prop.dadata_address.longitude
            }
        
        # Добавляем объект в ответ (фильтрация уже выполнена на уровне SQL)
        properties.append({
            'id': prop.id,
            'title': prop.title or 'Без названия',
            'address': prop.address or 'Адрес не указан',
            'dadata_address': dadata_address,
            'price': prop.price,
            'total_area': prop.total_area,
            'rooms_count': prop.rooms_count,
            'floor': prop.floor,
            'total_floors': prop.total_floors,
            'construction_year': prop.construction_year,
            'image': first_image,
            'longitude': prop.longitude,
            'latitude': prop.latitude,
            'rating': rating
        })
    
    return jsonify({
        'properties': properties,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@app.route('/api/complexes-light')
def get_complexes_light():
    """Легковесный API для быстрой загрузки списка ЖК"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Базовый запрос только с необходимыми полями
    query = ResidentialComplex.query.with_entities(
        ResidentialComplex.id,
        ResidentialComplex.name,
        ResidentialComplex.address,
        ResidentialComplex.developer_name,
        ResidentialComplex.photo_url,
        ResidentialComplex.latitude,
        ResidentialComplex.longitude
    )
    
    # Поиск
    q = request.args.get('q', '').strip()
    if q:
        query = query.filter(
            db.or_(
                ResidentialComplex.name.ilike(f'%{q}%'),
                ResidentialComplex.address.ilike(f'%{q}%')
            )
        )
    
    # Сортировка и пагинация
    pagination = query.order_by(ResidentialComplex.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Формируем легковесный ответ
    complexes = []
    for complex in pagination.items:
        complexes.append({
            'id': complex.id,
            'name': complex.name or 'Без названия',
            'address': complex.address or 'Адрес не указан',
            'developer_name': complex.developer_name,
            'photo_url': complex.photo_url,
            'latitude': complex.latitude,
            'longitude': complex.longitude
        })
    
    return jsonify({
        'complexes': complexes,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@app.route('/api/stats-light')
def get_stats_light():
    """Легковесная статистика для быстрой загрузки"""
    try:
        # Быстрые запросы для статистики
        total_properties = db.session.query(db.func.count(Property.id)).scalar()
        total_complexes = db.session.query(db.func.count(ResidentialComplex.id)).scalar()
        
        # Статистика по ценам
        price_stats = db.session.query(
            db.func.min(Property.price),
            db.func.max(Property.price),
            db.func.avg(Property.price)
        ).filter(Property.price.isnot(None)).first()
        
        # Статистика по комнатам
        rooms_stats = db.session.query(
            Property.rooms_count,
            db.func.count(Property.id)
        ).filter(Property.rooms_count.isnot(None)).group_by(Property.rooms_count).all()
        
        return jsonify({
            'total_properties': total_properties or 0,
            'total_complexes': total_complexes or 0,
            'price_stats': {
                'min': float(price_stats[0]) if price_stats[0] else 0,
                'max': float(price_stats[1]) if price_stats[1] else 0,
                'avg': float(price_stats[2]) if price_stats[2] else 0
            },
            'rooms_stats': {str(room): count for room, count in rooms_stats}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Создание индексов для ускорения запросов
def create_indexes():
    """Создает индексы для ускорения запросов"""
    try:
        # Индексы для таблицы Property
        db.engine.execute('CREATE INDEX IF NOT EXISTS idx_property_price ON property(price)')
        db.engine.execute('CREATE INDEX IF NOT EXISTS idx_property_total_area ON property(total_area)')
        db.engine.execute('CREATE INDEX IF NOT EXISTS idx_property_rooms_count ON property(rooms_count)')
        db.engine.execute('CREATE INDEX IF NOT EXISTS idx_property_address ON property(address)')
        db.engine.execute('CREATE INDEX IF NOT EXISTS idx_property_id_desc ON property(id DESC)')
        
        # Индексы для таблицы ResidentialComplex
        db.engine.execute('CREATE INDEX IF NOT EXISTS idx_complex_name ON residential_complex(name)')
        db.engine.execute('CREATE INDEX IF NOT EXISTS idx_complex_address ON residential_complex(address)')
        db.engine.execute('CREATE INDEX IF NOT EXISTS idx_complex_id_desc ON residential_complex(id DESC)')
        
        # Индексы для связанных таблиц
        db.engine.execute('CREATE INDEX IF NOT EXISTS idx_property_rating ON property_rating(property_id)')
        db.engine.execute('CREATE INDEX IF NOT EXISTS idx_property_yandex_rating ON property_yandex_rating(property_id)')
        db.engine.execute('CREATE INDEX IF NOT EXISTS idx_property_yandex_link ON property_yandex_link(property_id)')
        
        print("Индексы созданы успешно")
    except Exception as e:
        print(f"Ошибка при создании индексов: {e}")

# Вызываем создание индексов при запуске
    with app.app_context():
        create_indexes()

@app.route('/api/address-properties/<address_id>')
def get_address_properties(address_id):
    """Получение всех объектов недвижимости по адресу"""
    try:
        # Пытаемся получить адрес по ID
        address = Address.query.get(address_id)
        if not address:
            return jsonify({'error': 'Адрес не найден'}), 404
        
        # Получаем все объекты с этим адресом
        properties = Property.query.filter(
            Property.address_id == address_id
        ).options(
            db.joinedload(Property.rating_obj)
        ).all()
        
        # Формируем список объектов
        properties_list = []
        total_price = 0
        price_count = 0
        
        for prop in properties:
            # Получаем первое изображение
            first_image = None
            if prop.images:
                images_list = prop.images.split(',')
                if images_list:
                    first_image = images_list[0].strip()
            
            # Получаем рейтинг
            rating = None
            if hasattr(prop, 'rating_obj') and prop.rating_obj:
                rating = prop.rating_obj.rating
            
            # Проверяем, что данные корректные
            if (prop.id and prop.id > 0 and 
                prop.title and prop.title != 'nan' and 
                prop.address and prop.address != 'nan'):
                
                properties_list.append({
                    'id': prop.id,
                    'title': prop.title or 'Без названия',
                    'address': prop.address or 'Адрес не указан',
                    'price': prop.price,
                    'total_area': prop.total_area,
                    'rooms_count': prop.rooms_count,
                    'floor': prop.floor,
                    'total_floors': prop.total_floors,
                    'construction_year': prop.construction_year,
                    'image': first_image,
                    'longitude': prop.longitude,
                    'latitude': prop.latitude,
                    'rating': rating
                })
                
                if prop.price:
                    total_price += prop.price
                    price_count += 1
        
        # Вычисляем среднюю цену
        avg_price = total_price / price_count if price_count > 0 else 0
        
        return jsonify({
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
            'properties': properties_list,
            'total_properties': len(properties_list),
            'avg_price': avg_price,
            'statistics': {
                'total_properties': len(properties_list),
                'avg_price': avg_price
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/property/<int:property_id>')
def get_property_detail(property_id):
    """Получение детальной информации об объекте недвижимости"""
    try:
        # Получаем объект с предзагрузкой связанных данных
        property_item = Property.query.options(
            db.joinedload(Property.dadata_address),
            db.joinedload(Property.antiznak_status),
            db.joinedload(Property.rating_obj),
            db.joinedload(Property.yandex_rating_obj),
            db.joinedload(Property.yandex_link),
            db.joinedload(Property.generated_description_obj)
        ).get(property_id)
        
        if not property_item:
            return jsonify({'error': 'Объект не найден'}), 404
        
        # Получаем информацию об адресе
        address_info = None
        if property_item.dadata_address:
            address_info = {
                'id': property_item.dadata_address.id,
                'address': property_item.dadata_address.dadata_address,
                'full_address': property_item.dadata_address.dadata_full_address,
                'city': property_item.dadata_address.city,
                'street': property_item.dadata_address.street,
                'house': property_item.dadata_address.house,
                'latitude': property_item.dadata_address.latitude,
                'longitude': property_item.dadata_address.longitude
            }
        
        # Проверяем, был ли номер отправлен в КЦ
        sent_to_callcenter = False
        if property_item.contacts:
            import re
            phone_match = re.search(r'(\+?\d{10,15})', property_item.contacts)
            if phone_match:
                phone = phone_match.group(1)
                sent_to_callcenter = Lead2CallLog.query.filter_by(phone=phone, status='success').first() is not None
        
        # Найти связанный Яндекс-ЖК
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
            ).limit(5).all()  # Ограничиваем до 5 аналогичных
            
            for flat in flats:
                # Получаем первое изображение
                first_image = None
                if flat.images:
                    images_list = flat.images.split(',')
                    if images_list:
                        first_image = images_list[0].strip()
                
                same_flats.append({
                    'id': flat.id,
                    'title': flat.title or 'Без названия',
                    'address': flat.address or 'Адрес не указан',
                    'image': first_image,
                    'price': flat.price,
                    'total_area': flat.total_area,
                    'floor': flat.floor,
                    'total_floors': flat.total_floors,
                    'rating': flat.rating_obj.rating if getattr(flat, 'rating_obj', None) else None
                })
        
        # Формируем список изображений
        images = []
        if property_item.images:
            images = [img.strip() for img in property_item.images.split(',') if img.strip()]
        
        # Фотографии от Antiznak
        antiznak_photos = []
        if getattr(property_item, 'antiznak_status', None) and property_item.antiznak_status.photos:
            try:
                antiznak_photos = [p.replace('\\', '/').replace('\\', '/') for p in json.loads(property_item.antiznak_status.photos)]
            except:
                antiznak_photos = []
        
        # Объединяем все изображения
        all_images = images + antiznak_photos
        
        return jsonify({
            'id': property_item.id,
            'title': property_item.title or 'Без названия',
            'address': property_item.address or 'Адрес не указан',
            'price': property_item.price,
            'total_area': property_item.total_area,
            'living_area': property_item.living_area,
            'kitchen_area': property_item.kitchen_area,
            'rooms_count': property_item.rooms_count,
            'floor': property_item.floor,
            'total_floors': property_item.total_floors,
            'construction_year': property_item.construction_year,
            'content': property_item.content or '',
            'images': all_images,
            'contacts': property_item.contacts or '',
            'price_per_sqm': property_item.price_per_sqm,
            'longitude': property_item.longitude,
            'latitude': property_item.latitude,
            'dadata_address': address_info,
            'antiznak_status': getattr(property_item.antiznak_status, 'status', None),
            'source_url': property_item.source_url,
            'sent_to_callcenter': sent_to_callcenter,
            'rating': property_item.rating_obj.rating if getattr(property_item, 'rating_obj', None) else None,
            'yandex_rating': property_item.yandex_rating_obj.yandex_rating if getattr(property_item, 'yandex_rating_obj', None) else None,
            'yandex_complex_name': yandex_complex_name,
            'same_flats': same_flats,
            'generated_description': property_item.generated_description_obj.generated_description if getattr(property_item, 'generated_description_obj', None) else None,
            # Дополнительные поля
            'balcony': property_item.balcony,
            'loggia': property_item.loggia,
            'bathroom': property_item.bathroom,
            'toilet': property_item.toilet,
            'parking': property_item.parking,
            'security': property_item.security,
            'exclusive': property_item.exclusive,
            'delivery_quarter': property_item.delivery_quarter,
            'house_readiness': property_item.house_readiness
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-slugs', methods=['POST'])
def generate_slugs():
    """Генерирует slug для всех записей в таблице связей, где slug отсутствует"""
    try:
        # Получаем все записи без slug
        links_without_slug = PropertyYandexLink.query.filter(
            (PropertyYandexLink.slug.is_(None)) | (PropertyYandexLink.slug == '')
        ).all()
        
        updated_count = 0
        for link in links_without_slug:
            if link.yandex_complex_name:
                # Генерируем slug из названия комплекса
                slug = generate_slug(link.yandex_complex_name)
                
                # Проверяем уникальность slug
                counter = 1
                original_slug = slug
                while PropertyYandexLink.query.filter_by(slug=slug).first():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
                
                link.slug = slug
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Обновлено {updated_count} записей',
            'updated_count': updated_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/complexes-with-slugs')
def get_complexes_with_slugs():
    """Получить список комплексов с их slug"""
    try:
        # Получаем уникальные комплексы с slug
        complexes = db.session.query(
            PropertyYandexLink.yandex_complex_name,
            PropertyYandexLink.slug
        ).filter(
            PropertyYandexLink.yandex_complex_name.isnot(None),
            PropertyYandexLink.slug.isnot(None),
            PropertyYandexLink.slug != ''
        ).distinct().all()
        
        result = []
        for complex_name, slug in complexes:
            result.append({
                'complex_name': complex_name,
                'slug': slug
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/complex-slug/<complex_name>')
def get_complex_slug(complex_name):
    """Получить slug для конкретного комплекса по его названию"""
    import urllib.parse
    
    # Декодируем название комплекса из URL
    complex_name = urllib.parse.unquote(complex_name)
    
    # Получаем первую запись с этим названием комплекса
    link = PropertyYandexLink.query.filter_by(yandex_complex_name=complex_name).first()
    
    if not link or not link.slug:
        return jsonify({'error': 'Slug не найден'}), 404
    
    return jsonify({
        'complex_name': complex_name,
        'slug': link.slug
    })

@app.route('/api/property/<int:property_id>/last-price-change')
def get_last_price_change(property_id):
    """Получить последнее изменение цены объекта недвижимости"""
    try:
        # Получаем последнюю запись об изменении цены
        last_change = PriceHistory.query.filter_by(property_id=property_id)\
            .order_by(PriceHistory.changed_at.desc()).first()
        
        if not last_change:
            return jsonify({
                'success': True,
                'has_price_change': False,
                'message': 'История изменений цен не найдена'
            })
        
        # Определяем направление изменения
        change_direction = 'up' if last_change.price_change > 0 else 'down' if last_change.price_change < 0 else 'none'
        
        # Форматируем дату
        from datetime import datetime
        now = datetime.utcnow()
        time_diff = now - last_change.changed_at
        
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} дн. назад"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            time_ago = f"{hours} ч. назад"
        else:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes} мин. назад"
        
        return jsonify({
            'success': True,
            'has_price_change': True,
            'old_price': last_change.old_price,
            'new_price': last_change.new_price,
            'price_change': last_change.price_change,
            'change_percent': last_change.change_percent,
            'change_direction': change_direction,
            'changed_at': last_change.changed_at.isoformat(),
            'time_ago': time_ago,
            'changed_by': last_change.changed_by
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-address-slugs', methods=['POST'])
def generate_address_slugs():
    """Генерирует slug для всех адресов, у которых его нет"""
    try:
        addresses = Address.query.filter(Address.slug.is_(None)).all()
        generated_count = 0
        
        for address in addresses:
            # Создаем slug из адреса
            address_text = address.dadata_address or address.dadata_full_address or f"{address.street} {address.house}"
            if address_text:
                slug = generate_slug(address_text)
                
                # Проверяем уникальность
                counter = 1
                original_slug = slug
                while Address.query.filter_by(slug=slug).first():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
                
                address.slug = slug
                generated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Сгенерировано {generated_count} slug для адресов',
            'generated_count': generated_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/addresses-with-slugs')
def get_addresses_with_slugs():
    """Получить список адресов с их slug"""
    try:
        addresses = Address.query.filter(Address.slug.isnot(None)).all()
        
        result = []
        for address in addresses:
            result.append({
                'id': address.id,
                'address': address.dadata_address or address.dadata_full_address or f"{address.street} {address.house}",
                'slug': address.slug,
                'city': address.city,
                'street': address.street,
                'house': address.house
            })
        
        return jsonify({
            'success': True,
            'addresses': result,
            'total': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/address-slug/<address_id>')
def get_address_slug(address_id):
    """Получить slug для адреса по его ID"""
    try:
        address = Address.query.get(address_id)
        if not address:
            return jsonify({'success': False, 'error': 'Адрес не найден'}), 404
        
        if not address.slug:
            return jsonify({'success': False, 'error': 'Slug не найден'}), 404
        
        return jsonify({
            'success': True,
            'address_id': address.id,
            'slug': address.slug,
            'address': address.dadata_address or address.dadata_full_address or f"{address.street} {address.house}"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/address-properties-slug/<slug>')
def get_address_properties_by_slug(slug):
    """Получить объекты недвижимости по slug адреса"""
    try:
        address = Address.query.filter_by(slug=slug).first()
        if not address:
            return jsonify({'success': False, 'error': 'Адрес не найден'}), 404
        
        properties = Property.query.filter_by(address_id=address.id).all()
        
        result = []
        for prop in properties:
            result.append({
                'id': prop.id,
                'title': prop.title,
                'price': prop.price,
                'total_area': prop.total_area,
                'rooms_count': prop.rooms_count,
                'floor': prop.floor,
                'total_floors': prop.total_floors,
                'address': prop.address,
                'images': [img.strip() for img in prop.images.split(',')] if prop.images else [],
                'rating': getattr(prop, 'rating', None),
                'yandex_rating': getattr(prop, 'yandex_rating', None)
            })
        
        return jsonify({
            'success': True,
            'address': {
                'id': address.id,
                'address': address.dadata_address or address.dadata_full_address or f"{address.street} {address.house}",
                'slug': address.slug,
                'city': address.city,
                'street': address.street,
                'house': address.house
            },
            'properties': result,
            'total_properties': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_slug(text):
    """Генерирует slug из текста (транслитерация + очистка)"""
    import re
    import unicodedata
    
    # Транслитерация кириллицы
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    # Транслитерация
    for cyr, lat in translit_map.items():
        text = text.replace(cyr, lat)
    
    # Нормализация Unicode
    text = unicodedata.normalize('NFKD', text)
    
    # Замена спецсимволов на дефисы
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # Удаление начальных и конечных дефисов
    text = text.strip('-')
    
    # Приведение к нижнему регистру
    text = text.lower()
    
    return text


def create_slug_for_address(address_obj):
    """Создает уникальный slug для адреса"""
    if not address_obj.dadata_full_address:
        return None
    
    # Генерируем slug из полного адреса
    slug = generate_slug(address_obj.dadata_full_address)
    
    # Проверяем уникальность
    counter = 1
    original_slug = slug
    while Address.query.filter_by(slug=slug).first():
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    return slug

def create_slugs_for_all_addresses():
    """Создает slug'и для всех адресов, у которых их нет"""
    addresses_without_slugs = Address.query.filter(
        (Address.slug.is_(None)) | (Address.slug == '')
    ).all()
    
    created_count = 0
    for address in addresses_without_slugs:
        slug = create_slug_for_address(address)
        if slug:
            address.slug = slug
            created_count += 1
    
    db.session.commit()
    return created_count


@app.route('/api/create-address-slugs', methods=['POST'])
def api_create_address_slugs():
    """API endpoint для создания slug'ов для всех адресов"""
    try:
        created_count = create_slugs_for_all_addresses()
        return jsonify({
            'success': True,
            'created_count': created_count,
            'message': f'Создано {created_count} slug\'ов для адресов'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/complex/<int:complex_id>/properties')
def get_complex_properties_by_id(complex_id):
    """Получить все квартиры конкретного ЖК"""
    complex_obj = ResidentialComplex.query.get(complex_id)
    if not complex_obj:
        return jsonify({'error': 'ЖК не найден'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Получаем квартиры ЖК
    query = Property.query.filter_by(residential_complex_id=complex_id)
    
    # Сортировка по цене
    query = query.order_by(Property.price)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    properties = []
    for prop in pagination.items:
        properties.append({
            'id': prop.id,
            'title': prop.title,
            'address': prop.address,
            'price': prop.price,
            'price_per_sqm': prop.price_per_sqm,
            'total_area': prop.total_area,
            'rooms_count': prop.rooms_count,
            'floor': prop.floor,
            'total_floors': prop.total_floors,
            'construction_year': prop.construction_year,
            'contacts': prop.contacts,
            'images': prop.images,
            'latitude': prop.latitude,
            'longitude': prop.longitude
        })
    
    # Статистика ЖК
    total_properties = Property.query.filter_by(residential_complex_id=complex_id).count()
    avg_price = db.session.query(db.func.avg(Property.price)).filter_by(
        residential_complex_id=complex_id
    ).scalar() or 0
    
    return jsonify({
        'complex': {
            'id': complex_obj.id,
            'name': complex_obj.name,
            'address': complex_obj.address,
            'developer_name': complex_obj.developer_name,
            'ready_date': complex_obj.ready_date,
            'latitude': complex_obj.latitude,
            'longitude': complex_obj.longitude
        },
        'properties': properties,
        'statistics': {
            'total_properties': total_properties,
            'avg_price': avg_price
        },
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })

@app.route('/api/complex/<int:complex_id>')
def get_complex_detail(complex_id):
    """Получить детальную информацию о ЖК"""
    complex_obj = ResidentialComplex.query.get(complex_id)
    if not complex_obj:
        return jsonify({'error': 'ЖК не найден'}), 404
    
    # Статистика ЖК
    properties = Property.query.filter_by(residential_complex_id=complex_id).all()
    
    total_properties = len(properties)
    avg_price = sum(p.price for p in properties) / total_properties if total_properties > 0 else 0
    min_price = min(p.price for p in properties) if total_properties > 0 else 0
    max_price = max(p.price for p in properties) if total_properties > 0 else 0
    
    # Распределение по комнатам
    rooms_distribution = {}
    for prop in properties:
        rooms = prop.rooms_count or 0
        rooms_distribution[rooms] = rooms_distribution.get(rooms, 0) + 1
    
    return jsonify({
        'id': complex_obj.id,
        'name': complex_obj.name,
        'address': complex_obj.address,
        'short_address': complex_obj.short_address,
        'developer_name': complex_obj.developer_name,
        'developer_full_name': complex_obj.developer_full_name,
        'developer_inn': complex_obj.developer_inn,
        'min_floor': complex_obj.min_floor,
        'max_floor': complex_obj.max_floor,
        'ready_date': complex_obj.ready_date,
        'status': complex_obj.status,
        'build_type': complex_obj.build_type,
        'photo_url': complex_obj.photo_url,
        'latitude': complex_obj.latitude,
        'longitude': complex_obj.longitude,
        'statistics': {
            'total_properties': total_properties,
            'avg_price': avg_price,
            'min_price': min_price,
            'max_price': max_price,
            'rooms_distribution': rooms_distribution
        }
    })

@app.route('/api/residential-complexes')
def get_residential_complexes():
    """Получить уникальные жилые комплексы с данными из Yandex (только с квартирами)"""
    try:
        yandex_complexes = db.session.query(
            YandexNewBuilding.id,
            YandexNewBuilding.complex_name,
            YandexNewBuilding.region,
            YandexNewBuilding.address,
            YandexNewBuilding.ready_date,
            YandexNewBuilding.queue,
            YandexNewBuilding.url,
            YandexNewBuilding.trend_block_id
        ).filter(
            YandexNewBuilding.complex_name.isnot(None),
            YandexNewBuilding.complex_name != ''
        ).all()

        stats = db.session.query(
            Property.yandex_complex_id,
            db.func.count(Property.id).label('count'),
            db.func.avg(Property.price).label('avg_price'),
            db.func.min(Property.price).label('min_price'),
            db.func.max(Property.price).label('max_price')
        ).group_by(Property.yandex_complex_id).all()
        stats_map = {s.yandex_complex_id: s for s in stats}

        complexes_data = []
        for yc in yandex_complexes:
            s = stats_map.get(yc.id)
            if not s or s.count == 0:
                continue  # Пропускаем комплексы без квартир
            
            # Получаем фотографии из trend_block
            photos = []
            if yc.trend_block_id:
                trend_block = TrendBlock.query.get(yc.trend_block_id)
                if trend_block and trend_block.renderer:
                    try:
                        renderer_data = json.loads(trend_block.renderer)
                        if isinstance(renderer_data, list):
                            photos = renderer_data
                    except:
                        pass
            
            complex_data = {
                'id': yc.id,
                'name': yc.complex_name,
                'region': yc.region,
                'address': yc.address,
                'ready_date': yc.ready_date,
                'queue': yc.queue,
                'url': yc.url,
                'properties_count': s.count,
                'avg_price': float(s.avg_price) if s.avg_price else 0,
                'min_price': float(s.min_price) if s.min_price else 0,
                'max_price': float(s.max_price) if s.max_price else 0,
                'photos': photos,
                'trend_building': None
            }
            complexes_data.append(complex_data)

        return jsonify({
            'success': True,
            'complexes': complexes_data,
            'total': len(complexes_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/residential-complex/<int:complex_id>/properties')
def get_residential_complex_properties(complex_id):
    """Получить квартиры конкретного жилого комплекса"""
    try:
        # Получаем информацию о ЖК
        yandex_complex = YandexNewBuilding.query.get(complex_id)
        if not yandex_complex:
            return jsonify({'success': False, 'error': 'ЖК не найден'}), 404
        # Получаем квартиры в этом ЖК
        properties = Property.query.filter_by(yandex_complex_id=complex_id).all()
        # Получаем статистику цен
        price_stats = db.session.query(
            db.func.avg(Property.price).label('avg_price'),
            db.func.min(Property.price).label('min_price'),
            db.func.max(Property.price).label('max_price'),
            db.func.count(Property.id).label('total_properties')
        ).filter_by(yandex_complex_id=complex_id).first()
        # Получаем фото из trend_block
        renderer_photos = []
        plan_photos = []
        if yandex_complex.trend_block_id:
            trend_block = TrendBlock.query.get(yandex_complex.trend_block_id)
            if trend_block:
                # Получаем рендеры
                if trend_block.renderer:
                    try:
                        renderer_data = json.loads(trend_block.renderer)
                        if isinstance(renderer_data, list):
                            renderer_photos = renderer_data
                    except:
                        pass
                
                # Получаем планы
                if trend_block.plan:
                    try:
                        plan_data = json.loads(trend_block.plan)
                        if isinstance(plan_data, list):
                            plan_photos = plan_data
                    except:
                        pass
        # Формируем ответ
        complex_data = {
            'id': yandex_complex.id,
            'name': yandex_complex.complex_name,
            'region': yandex_complex.region,
            'address': yandex_complex.address,
            'ready_date': yandex_complex.ready_date,
            'queue': yandex_complex.queue,
            'url': yandex_complex.url,
            'renderer_photos': renderer_photos,
            'plan_photos': plan_photos
        }
        statistics = {
            'avg_price': float(price_stats.avg_price) if price_stats.avg_price else 0,
            'min_price': float(price_stats.min_price) if price_stats.min_price else 0,
            'max_price': float(price_stats.max_price) if price_stats.max_price else 0,
            'total_properties': price_stats.total_properties
        }
        properties_data = []
        for prop in properties:
            # Получаем фото квартиры из поля images
            images = []
            if prop.images:
                images = [img.strip() for img in prop.images.split(',') if img.strip()]
            properties_data.append({
                'id': prop.id,
                'title': prop.title,
                'price': prop.price,
                'images': images,
                'address': prop.address,
                'dadata_address': prop.dadata_address.dadata_address if prop.dadata_address else None,
                'total_area': prop.total_area,
                'rooms_count': prop.rooms_count,
                'floor': prop.floor,
                'total_floors': prop.total_floors,
                'rating': prop.rating_obj.rating if getattr(prop, 'rating_obj', None) else None
            })
        return jsonify({
            'success': True,
            'complex': complex_data,
            'statistics': statistics,
            'properties': properties_data
        })
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({'success': False, 'error': str(e), 'traceback': tb}), 500

@app.route('/api/search', methods=['GET'])
def search_complexes():
    """Быстрый поиск жилых комплексов по строке поиска (только комплексы с квартирами)"""
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify({'complexes': []})

        # Быстрый SQL-запрос: только комплексы с квартирами и совпадением по complex_name
        query_lower = query.lower()
        complexes = (
            db.session.query(YandexNewBuilding)
            .filter(
                func.lower(YandexNewBuilding.complex_name).ilike(f'%{query_lower}%'),
                db.session.query(Property.id)
                    .filter(Property.yandex_complex_id == YandexNewBuilding.id)
                    .exists()
            )
            .limit(10)
            .all()
        )

        result = []
        for complex in complexes:
            properties_count = Property.query.filter_by(yandex_complex_id=complex.id).count()
            result.append({
                'id': complex.id,
                'name': complex.complex_name,
                'properties_count': properties_count
            })

        return jsonify({'complexes': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sale-properties')
def get_sale_properties():
    """Получить объекты со скидками (сниженными ценами)"""
    try:
        # Получаем объекты с историей изменения цен
        # Ищем объекты, у которых есть записи в price_history с отрицательным price_change
        properties_with_discounts = db.session.query(Property).join(
            PriceHistory, Property.id == PriceHistory.property_id
        ).filter(
            PriceHistory.price_change < 0  # Только снижения цен
        ).order_by(
            PriceHistory.price_change.asc()  # Максимальные скидки сверху
        ).limit(48).all()
        
        # Если объектов со скидками мало, добавляем объекты с самыми низкими ценами за м²
        if len(properties_with_discounts) < 24:
            additional_properties = db.session.query(Property).filter(
                Property.price_per_sqm.isnot(None),
                Property.price_per_sqm > 0
            ).order_by(
                Property.price_per_sqm.asc()  # Самые дешевые сверху
            ).limit(48 - len(properties_with_discounts)).all()
            
            # Объединяем списки, избегая дубликатов
            all_properties = list(properties_with_discounts)
            existing_ids = {p.id for p in properties_with_discounts}
            
            for prop in additional_properties:
                if prop.id not in existing_ids:
                    all_properties.append(prop)
                    existing_ids.add(prop.id)
        else:
            all_properties = properties_with_discounts
        
        # Формируем ответ
        properties_data = []
        for prop in all_properties:
            # Получаем последнее изменение цены
            last_price_change = db.session.query(PriceHistory).filter(
                PriceHistory.property_id == prop.id
            ).order_by(PriceHistory.changed_at.desc()).first()
            
            # Получаем рейтинг
            rating = db.session.query(PropertyRating.rating).filter(
                PropertyRating.property_id == prop.id
            ).scalar()
            
            # Парсим изображения
            images = []
            if prop.images:
                try:
                    # Пробуем парсить как JSON
                    images = json.loads(prop.images)
                except:
                    # Если не JSON, то это строка с URL через запятую
                    if prop.images:
                        images = [img.strip() for img in prop.images.split(',') if img.strip()]
            
            property_data = {
                'id': prop.id,
                'title': prop.title,
                'price': prop.price,
                'price_per_sqm': prop.price_per_sqm,
                'total_area': prop.total_area,
                'rooms_count': prop.rooms_count,
                'floor': prop.floor,
                'total_floors': prop.total_floors,
                'construction_year': prop.construction_year,
                'address': prop.address,
                'longitude': prop.longitude,
                'latitude': prop.latitude,
                'image': images[0] if images else None,
                'images': images,
                'rating': rating,
                'price_change': last_price_change.price_change if last_price_change else None,
                'change_percent': last_price_change.change_percent if last_price_change else None
            }
            
            # Добавляем информацию об адресе
            if prop.dadata_address:
                property_data['dadata_address'] = {
                    'id': prop.dadata_address.id,
                    'address': prop.dadata_address.dadata_address,
                    'full_address': prop.dadata_address.dadata_full_address,
                    'city': prop.dadata_address.city,
                    'street': prop.dadata_address.street,
                    'house': prop.dadata_address.house,
                    'latitude': prop.dadata_address.latitude,
                    'longitude': prop.dadata_address.longitude
                }
            
            properties_data.append(property_data)
        
        return jsonify({
            'success': True,
            'properties': properties_data,
            'total': len(properties_data)
        })
        
    except Exception as e:
        print(f"Error getting sale properties: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'properties': [],
            'total': 0
        })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
