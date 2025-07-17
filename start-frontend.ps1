Write-Host "Запуск Frontend (React)..." -ForegroundColor Green
Write-Host "Приложение будет доступно по адресу: http://localhost:8081" -ForegroundColor Yellow
Write-Host "Для остановки нажмите Ctrl+C" -ForegroundColor Red
Write-Host ""

Set-Location frontend\cozy-catalog-haven
npm run dev 