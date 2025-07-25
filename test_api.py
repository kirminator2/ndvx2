import requests
import json

def test_api():
    base_url = "http://localhost:5000/api"
    
    # Тест 1: Получение списка жилых комплексов
    print("Тестируем API жилых комплексов...")
    try:
        response = requests.get(f"{base_url}/residential-complexes")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Успешно! Найдено комплексов: {len(data.get('complexes', []))}")
            if data.get('complexes'):
                print(f"Первый комплекс: {data['complexes'][0].get('name', 'N/A')}")
        else:
            print(f"Ошибка: {response.text}")
    except Exception as e:
        print(f"Ошибка запроса: {e}")
    
    # Тест 2: Получение квартир конкретного комплекса
    print("\nТестируем API квартир в комплексе...")
    try:
        response = requests.get(f"{base_url}/residential-complex/1/properties")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Успешно! Найдено квартир: {len(data.get('properties', []))}")
        else:
            print(f"Ошибка: {response.text}")
    except Exception as e:
        print(f"Ошибка запроса: {e}")

if __name__ == "__main__":
    test_api() 