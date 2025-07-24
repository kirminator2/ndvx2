#!/usr/bin/env python3
"""
Скрипт для тестирования производительности API endpoints
"""

import requests
import time
import statistics
from datetime import datetime

API_BASE_URL = "http://localhost:5000/api"

def test_endpoint(endpoint, params=None, iterations=10):
    """Тестирует производительность endpoint"""
    url = f"{API_BASE_URL}/{endpoint}"
    response_times = []
    
    print(f"\nТестирование {endpoint}...")
    
    for i in range(iterations):
        start_time = time.time()
        
        try:
            response = requests.get(url, params=params, timeout=30)
            end_time = time.time()
            
            if response.status_code == 200:
                response_time = (end_time - start_time) * 1000  # в миллисекундах
                response_times.append(response_time)
                print(f"  Запрос {i+1}: {response_time:.2f}ms")
            else:
                print(f"  Запрос {i+1}: Ошибка {response.status_code}")
                
        except Exception as e:
            print(f"  Запрос {i+1}: Ошибка - {e}")
    
    if response_times:
        avg_time = statistics.mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        median_time = statistics.median(response_times)
        
        print(f"\nРезультаты для {endpoint}:")
        print(f"  Среднее время: {avg_time:.2f}ms")
        print(f"  Минимальное время: {min_time:.2f}ms")
        print(f"  Максимальное время: {max_time:.2f}ms")
        print(f"  Медиана: {median_time:.2f}ms")
        
        return {
            'endpoint': endpoint,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'median_time': median_time,
            'iterations': len(response_times)
        }
    
    return None

def main():
    """Основная функция тестирования"""
    print("=== Тестирование производительности API ===")
    print(f"Время начала: {datetime.now()}")
    
    # Тестируем различные endpoints
    tests = [
        # Старый тяжелый API
        ('properties', {'per_page': 50}),
        
        # Новый легковесный API
        ('properties-light', {'per_page': 20}),
        ('properties-light', {'per_page': 50}),
        
        # API для ЖК
        ('complexes-light', {'per_page': 10}),
        
        # Статистика
        ('stats-light', None),
        
        # Фильтрованные запросы
        ('properties-light', {'price_min': 1000000, 'price_max': 5000000}),
        ('properties-light', {'rooms': 2}),
        ('properties-light', {'q': 'Краснодар'}),
    ]
    
    results = []
    
    for endpoint, params in tests:
        result = test_endpoint(endpoint, params)
        if result:
            results.append(result)
    
    # Выводим сводку
    print("\n" + "="*50)
    print("СВОДКА РЕЗУЛЬТАТОВ")
    print("="*50)
    
    for result in results:
        print(f"\n{result['endpoint']}:")
        print(f"  Среднее время: {result['avg_time']:.2f}ms")
        print(f"  Диапазон: {result['min_time']:.2f}ms - {result['max_time']:.2f}ms")
    
    # Сравнение старого и нового API
    old_api = next((r for r in results if r['endpoint'] == 'properties'), None)
    new_api = next((r for r in results if r['endpoint'] == 'properties-light' and r.get('params', {}).get('per_page') == 20), None)
    
    if old_api and new_api:
        improvement = ((old_api['avg_time'] - new_api['avg_time']) / old_api['avg_time']) * 100
        print(f"\nУлучшение производительности:")
        print(f"  Старый API: {old_api['avg_time']:.2f}ms")
        print(f"  Новый API: {new_api['avg_time']:.2f}ms")
        print(f"  Улучшение: {improvement:.1f}%")

if __name__ == "__main__":
    main() 