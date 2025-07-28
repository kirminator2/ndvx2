@echo off
echo Запуск полного стека приложения...
echo Backend будет доступен по адресу: http://localhost:5000
echo Frontend будет доступен по адресу: http://localhost:8081
echo.

echo Установка зависимостей backend...
call .venv\Scripts\activate.bat
cd backend
pip install -r requirements.txt
cd ..

echo.
echo Запуск Backend...
start "Backend" cmd /k "cd backend && call ..\\.venv\\Scripts\\activate.bat && python app.py"

echo.
echo Запуск Frontend в production режиме...
start "Frontend" cmd /k "cd frontend\cozy-catalog-haven && set NODE_ENV=production && npm run build && npm run preview"

echo.
echo Оба приложения запущены!
echo Нажмите любую клавишу для закрытия этого окна...
pause 