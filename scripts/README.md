Crear o reemplazar modelo basado en Modelfile

    ollama create <modelo> -f ./Modelfile

    ollama create sql-football -f sql-football.Modelfile


├── application/
│   ├── ai/                          # Nueva carpeta para IA
│   │   ├── __init__.py
│   │   ├── llm_services.py          # Servicios de LLM (Ollama)
│   │   ├── chain_services.py        # Cadenas de LangChain
│   │   ├── prompt_templates.py      # Plantillas de prompts
│   │   ├── agents/                  # Agentes especializados
│   │   │   ├── __init__.py
│   │   │   ├── data_processor.py    # Procesador de datos
│   │   │   └── query_analyzer.py    # Analizador de consultas
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── text_processing.py   # Utilidades de texto
│   │       └── validation.py        # Validación de respuestas AI
│   ├── apis.py                      # EXISTENTE - Endpoints REST
│   ├── services.py                  # EXISTENTE - Servicios de BD
│   ├── models.py                    # EXISTENTE - Modelos de BD
│   ├── ollama.py                    # RENOMBRAR o adaptar
│   └── views.py                     # EXISTENTE - Vistas Flask