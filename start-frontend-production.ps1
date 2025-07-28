Write-Host "Запуск Frontend (React) в production режиме..." -ForegroundColor Green
Write-Host "Приложение будет доступно по адресу: http://localhost:8081" -ForegroundColor Yellow
Write-Host "Для остановки нажмите Ctrl+C" -ForegroundColor Red
Write-Host ""

Set-Location frontend\cozy-catalog-haven

# Устанавливаем переменную окружения для production
$env:NODE_ENV = "production"

# Собираем приложение для production
Write-Host "Сборка приложения для production..." -ForegroundColor Cyan
npm run build

# Запускаем preview сервер для production сборки
Write-Host "Запуск preview сервера..." -ForegroundColor Cyan
npm run preview 