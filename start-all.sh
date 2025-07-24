#!/bin/bash

echo "Запуск полного стека приложения..."
echo "Backend будет доступен по адресу: http://localhost:5000"
echo "Frontend будет доступен по адресу: http://localhost:8081"
echo ""

# Проверяем, существует ли виртуальное окружение
if [ ! -d ".venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv .venv
fi

# Активируем виртуальное окружение
source .venv/bin/activate

# Устанавливаем зависимости backend
echo "Установка зависимостей backend..."
cd backend
pip install -r requirements.txt
cd ..

# Проверяем существование frontend папки и package.json
if [ ! -d "frontend/cozy-catalog-haven" ]; then
    echo "ОШИБКА: Папка frontend/cozy-catalog-haven не найдена!"
    exit 1
fi

if [ ! -f "frontend/cozy-catalog-haven/package.json" ]; then
    echo "ОШИБКА: package.json не найден в frontend/cozy-catalog-haven!"
    exit 1
fi

# Устанавливаем зависимости frontend
echo "Установка зависимостей frontend..."
cd frontend/cozy-catalog-haven
echo "Текущая директория: $(pwd)"
echo "Проверка package.json: $(ls -la package.json)"
npm install
cd ../..

echo ""
echo "Запуск Backend..."
# Запускаем backend в фоне
cd backend
source ../.venv/bin/activate
python app.py &
BACKEND_PID=$!
cd ..

echo "Запуск Frontend..."
# Запускаем frontend в фоне
cd frontend/cozy-catalog-haven
echo "Запуск frontend из директории: $(pwd)"
npm run dev &
FRONTEND_PID=$!
cd ../..

echo ""
echo "Оба приложения запущены!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Для остановки приложений нажмите Ctrl+C"
echo "Или выполните: kill $BACKEND_PID $FRONTEND_PID"

# Ждем сигнала для остановки
trap "echo 'Остановка приложений...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Ждем завершения процессов
wait 