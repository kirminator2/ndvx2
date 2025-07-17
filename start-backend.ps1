Write-HostЗапуск Backend (Flask API)... -ForegroundColor Green
Write-HostПриложение будет доступно по адресу: http://localhost:5000 -ForegroundColor Yellow
Write-Host Для остановки нажмите Ctrl+C -ForegroundColor Red
Write-Host ""

Set-Location backend
& ..\\.venv\\Scripts\\Activate.ps1"
python app.py 