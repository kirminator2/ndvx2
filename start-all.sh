#!/bin/bash

echo "Запуск полного стека приложения..."
echo "Backend будет доступен по адресу: http://localhost:5000"
echo "Frontend будет доступен по адресу: http://localhost:8081"

# Проверяем наличие npm
if ! command -v npm &> /dev/null; then
    echo "ОШИБКА: npm не найден!"
    echo "Установите Node.js и npm:"
    echo "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -"
    echo "sudo apt-get install -y nodejs"
    exit 1
fi

# Проверяем, занят ли порт 5000
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
    echo "ПРЕДУПРЕЖДЕНИЕ: Порт 5000 уже занят!"
    echo "Останавливаем процесс на порту 5000..."
    sudo lsof -ti:5000 | xargs kill -9
fi

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

# Устанавливаем зависимости frontend
echo "Установка зависимостей frontend..."
cd frontend/cozy-catalog-haven
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