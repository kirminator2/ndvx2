@echo off
echo Запуск Backend (Flask API)...
echo Приложение будет доступно по адресу: http://localhost:5000
echo Для остановки нажмите Ctrl+C
echo.
cd backend
call ..\\.venv\\Scripts\\activate.bat
call ..\\.venv\\Scripts\\python.exe app.py
pause 