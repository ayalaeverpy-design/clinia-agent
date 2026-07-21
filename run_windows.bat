@echo off
if not exist .venv\Scripts\python.exe (
  echo No se encontro el entorno virtual. Ejecuta primero setup_windows.ps1
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m streamlit run app.py
