Write-Host "Запуск полного стека приложения..." -ForegroundColor Green
Write-Host "Backend будет доступен по адресу: http://localhost:5000" -ForegroundColor Yellow
Write-Host "Frontend будет доступен по адресу: http://localhost:8081" -ForegroundColor Yellow
Write-Host ""

Write-Host "Запуск Backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PWD\backend'; & $PWD\.venv\Scripts\Activate.ps1; python app.py" -WindowStyle Normal

Write-Host "Запуск Frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PWD\frontend\cozy-catalog-haven'; npm run dev" -WindowStyle Normal

Write-Host "Оба приложения запущены!" -ForegroundColor Green
Write-Host "Нажмите любую клавишу для закрытия этого окна..." -ForegroundColor Yellow
Read-Host 