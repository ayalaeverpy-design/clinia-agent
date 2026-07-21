# ClinIA — Asistente Inteligente para Consultorio Médico

ClinIA es un proyecto académico que construye un agente de inteligencia artificial para responder consultas administrativas usando documentos ficticios de la **Clínica Vida Plena**.

## Estado actual

- ✅ Lectura de documentos PDF y CSV.
- ✅ Normalización y conservación de metadatos.
- ✅ Fragmentación de textos con solapamiento.
- ✅ Recuperación local de fragmentos mediante BM25.
- ⏳ Integración con OCI Generative AI.
- ⏳ Generación final de respuestas con fuentes.
- ⏳ Deploy público en OCI.

## Ejecutar en Windows

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abrir en el navegador:

```text
http://localhost:8501
```

## Ejecutar pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Probar la recuperación desde consola

```powershell
.\.venv\Scripts\python.exe scripts\test_retrieval.py
```

## Preguntas de prueba

- ¿Con cuánta anticipación puedo cancelar un turno?
- ¿Qué documentos tengo que llevar a la consulta?
- ¿Cómo protege la clínica mis datos personales?
- ¿Qué cobertura tiene el plan Integral de SaludPlus?

## Alcance y seguridad

Todos los datos son ficticios. ClinIA brinda información administrativa y no realiza diagnósticos ni recomienda medicamentos.
