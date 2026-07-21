$ErrorActionPreference = "Stop"

Write-Host "Creando entorno virtual..." -ForegroundColor Cyan
py -m venv .venv

Write-Host "Instalando dependencias..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

Write-Host "Probando lectura de documentos..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe scripts\test_document_loading.py

Write-Host "Ejecutando pruebas..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pytest

Write-Host "Configuración terminada." -ForegroundColor Green
Write-Host "Para abrir la aplicación ejecutá:" -ForegroundColor Yellow
Write-Host ".\.venv\Scripts\python.exe -m streamlit run app.py"
