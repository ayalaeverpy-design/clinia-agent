# ClinIA — Asistente Inteligente para Consultorio Médico

ClinIA es un proyecto académico para el Challenge Alura Agente. El objetivo es crear un agente capaz de responder preguntas administrativas basándose en documentos PDF y CSV de una clínica ficticia.

> **Aviso:** toda la información de Clínica Vida Plena, sus convenios y políticas es ficticia y se utiliza únicamente con fines educativos.

## Estado actual

- [x] Documentos ficticios en PDF y CSV.
- [x] Lectura de PDF con `pypdf`.
- [x] Lectura de CSV con `pandas`.
- [x] Interfaz inicial en Streamlit.
- [x] Pruebas automáticas de carga documental.
- [ ] Fragmentación de documentos para RAG.
- [ ] Embeddings y búsqueda semántica.
- [ ] Integración con OCI Generative AI.
- [ ] Respuestas con fuentes.
- [ ] Deploy en OCI.

## Estructura

```text
clinia-agent/
├── app.py
├── data/
├── docs/
├── screenshots/
├── scripts/
├── src/
├── tests/
├── requirements.txt
├── requirements-dev.txt
├── setup_windows.ps1
└── run_windows.bat
```

## Requisitos

- Python 3.11 o 3.12 recomendado.
- Git.
- Acceso posterior a Oracle Cloud Infrastructure.

## Instalación en Windows

Abrir PowerShell en la carpeta del proyecto y ejecutar:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_windows.ps1
```

También puede realizarse manualmente:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python scripts\test_document_loading.py
python -m pytest
```

## Ejecutar la aplicación

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

O mediante doble clic en `run_windows.bat` después de completar la instalación.

## Alcance de seguridad

ClinIA debe responder solamente consultas administrativas basadas en los documentos. No debe diagnosticar enfermedades, indicar medicamentos ni reemplazar a profesionales de salud.
