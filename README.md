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

3. Запустите приложение:
   ```bash
   npm run dev
   ```

4. Откройте в браузере: http://localhost:5173

## Новые возможности

### Улучшенная работа с данными Яндекс-ЖК

**Основные изменения:**
- **Сохранение данных**: Старые данные Яндекс-ЖК больше не удаляются при импорте
- **Обновление существующих**: При импорте обновляются существующие записи и добавляются новые
- **Сохранение связей**: Связи между объектами и Яндекс-ЖК сохраняются при обновлении
- **Автоматические slug'и**: При создании новых связей автоматически генерируются slug'и

**API endpoints:**
- `POST /api/import-yandex-newbuildings` - Импорт с сохранением данных
- `POST /api/update-yandex-links` - Обновление связей без удаления
- `POST /api/create-yandex-link-slugs` - Создание slug'ов для связей

**Результат импорта:**
```json
{
  "success": true,
  "added_count": 450,      // Новые записи
  "updated_count": 71321,  // Обновленные записи
  "message": "Импорт Яндекс-ЖК завершен"
}
```

**Результат обновления связей:**
```json
{
  "success": true,
  "new_links_created": 0,        // Новые связи
  "existing_links_updated": 3090 // Обновленные связи
}
```

## API Документация

Полная документация API доступна по адресу: http://localhost:5000/api-docs 