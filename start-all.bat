@echo off
echo Запуск полного стека приложения...
echo Backend будет доступен по адресу: http://localhost:5000
echo Frontend будет доступен по адресу: http://localhost:8081
echo.
echo Запуск Backend...
start "Backend" cmd /k "cd backend && call ..\\.venv\\Scripts\\activate.bat && call ..\\.venv\\Scripts\\python.exe app.py"
echo.
echo Запуск Frontend...
start "Frontend" cmd /k "cd frontend\cozy-catalog-haven && npm run dev"
echo.
echo Оба приложения запущены!
echo Нажмите любую клавишу для закрытия этого окна...
pause 