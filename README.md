# Недвижимость - Админка и API

Проект состоит из двух частей:
- **Backend** - Flask API и админка
- **Frontend** - React приложение

## Структура проекта

```
ndvx2/
├── backend/          # Flask приложение
│   ├── app.py       # Основной файл приложения
│   ├── requirements.txt
│   ├── templates/   # HTML шаблоны
│   ├── instance/    # База данных
│   └── photos/      # Фотографии объектов
├── frontend/        # React приложение
│   └── cozy-catalog-haven/  # React приложение
│       ├── src/
│       ├── package.json
│       └── public/
├── .venv/           # Виртуальное окружение Python
└── README.md
```

## Быстрый старт

### PowerShell (рекомендуется)

**Запуск Backend:**
```powershell
.\start-backend.ps1
```

**Запуск Frontend:**
```powershell
.\start-frontend.ps1
```

**Запуск обоих приложений:**
```powershell
.\start-all.ps1
```

### Batch файлы

**Запуск Backend:**
```cmd
.\start-backend.bat
```

**Запуск Frontend:**
```cmd
.\start-frontend.bat
```

**Запуск обоих приложений:**
```cmd
.\start-all.bat
```

### Ручной запуск

#### Backend (Flask API)

1. Активируйте виртуальное окружение:
   ```bash
   .venv\Scripts\Activate.ps1 # PowerShell
   # или
   .venv\Scripts\activate.bat  # CMD
   ```

2. Перейдите в папку backend:
   ```bash
   cd backend
   ```

3. Установите зависимости (если не установлены):
   ```bash
   pip install -r requirements.txt
   ```

4. Запустите приложение:
   ```bash
   python app.py
   ```

5. Откройте в браузере: http://localhost:5000/admin

#### Frontend (React)

1. Перейдите в папку frontend/cozy-catalog-haven:
   ```bash
   cd frontend\cozy-catalog-haven
   ```

2. Установите зависимости (если не установлены):
   ```bash
   npm install
   ```

3. Запустите в режиме разработки:
   ```bash
   npm run dev
   ```

4. Откройте в браузере: http://localhost:8081

## API Endpoints

### Основные endpoints:
- `GET /api/properties` - список объектов недвижимости
- `GET /api/complexes` - список жилых комплексов
- `GET /api/yandex-newbuildings` - Яндекс-ЖК
- `GET /api/complexes-with-properties` - ЖК с квартирами

### Новые endpoints для ЖК:
- `GET /api/complex-info/{complex_name}` - информация о ЖК
- `GET /api/complex-properties/{complex_name}` - квартиры ЖК

## Документация

- [Быстрый старт](БЫСТРЫЙ_СТАРТ.md)
- [Инструкция](ИНСТРУКЦИЯ.md)
- [Что сделано](ЧТО_СДЕЛАНО.md)
- [Новые возможности](НОВЫЕ_ВОЗМОЖНОСТИ.md) 