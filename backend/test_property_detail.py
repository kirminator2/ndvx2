#!/usr/bin/env python3
"""
Простой тест для проверки API детальной информации об объекте
"""

import requests
import json

API_BASE_URL = "http://localhost:5000/api"

def test_property_detail():
    """Тестирует API детальной информации об объекте"""
    
    # Сначала получаем список объектов
    print("Получение списка объектов...")
    response = requests.get(f"{API_BASE_URL}/properties-light?per_page=1")
    
    if response.status_code != 200:
        print(f"Ошибка получения списка объектов: {response.status_code}")
        return
    
    data = response.json()
    if not data.get('properties'):
        print("Нет объектов для тестирования")
        return
    
    # Берем первый объект
    property_id = data['properties'][0]['id']
    print(f"Тестируем объект с ID: {property_id}")
    
    # Получаем детальную информацию
    print(f"\nПолучение детальной информации для объекта {property_id}...")
    detail_response = requests.get(f"{API_BASE_URL}/property/{property_id}")
    
    if detail_response.status_code != 200:
        print(f"Ошибка получения детальной информации: {detail_response.status_code}")
        print(f"Ответ: {detail_response.text}")
        return
    
    detail_data = detail_response.json()
    
    # Выводим основную информацию
    print(f"\n✅ Детальная информация получена успешно!")
    print(f"ID: {detail_data.get('id')}")
    print(f"Название: {detail_data.get('title')}")
    print(f"Адрес: {detail_data.get('address')}")
    print(f"Цена: {detail_data.get('price')} ₽")
    print(f"Площадь: {detail_data.get('total_area')} м²")
    print(f"Комнат: {detail_data.get('rooms_count')}")
    print(f"Этаж: {detail_data.get('floor')}/{detail_data.get('total_floors')}")
    
    # Проверяем наличие изображений
    images = detail_data.get('images', [])
    print(f"Количество изображений: {len(images)}")
    if images:
        print(f"Первое изображение: {images[0]}")
    
    # Проверяем аналогичные объекты
    same_flats = detail_data.get('same_flats', [])
    print(f"Аналогичных объектов: {len(same_flats)}")
    
    # Проверяем рейтинги
    rating = detail_data.get('rating')
    yandex_rating = detail_data.get('yandex_rating')
    if rating:
        print(f"Рейтинг: {rating}")
    if yandex_rating:
        print(f"Рейтинг Яндекс: {yandex_rating}")
    
    # Проверяем контакты
    contacts = detail_data.get('contacts')
    if contacts:
        print(f"Контакты: {contacts}")
    
    # Проверяем ЖК
    yandex_complex = detail_data.get('yandex_complex_name')
    if yandex_complex:
        print(f"ЖК: {yandex_complex}")
    
    print(f"\n📊 Размер ответа: {len(json.dumps(detail_data))} символов")
    
    return detail_data

def test_invalid_property():
    """Тестирует запрос несуществующего объекта"""
    print("\nТестирование несуществующего объекта...")
    response = requests.get(f"{API_BASE_URL}/property/999999")
    
    if response.status_code == 404:
        print("✅ Правильно обработана ошибка 404 для несуществующего объекта")
    else:
        print(f"❌ Неожиданный статус: {response.status_code}")

if __name__ == "__main__":
    print("=== Тестирование API детальной информации об объекте ===")
    
    try:
        # Тестируем существующий объект
        test_property_detail()
        
        # Тестируем несуществующий объект
        test_invalid_property()
        
        print("\n✅ Все тесты завершены!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к серверу. Убедитесь, что сервер запущен.")
    except Exception as e:
        print(f"❌ Ошибка: {e}") 