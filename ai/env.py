# ai/env.py
"""
Carga .env y expone helpers de configuración.
Debe importarse ANTES de ai.services.* para que OLLAMA_MODEL
esté disponible cuando retrieval.py calcula MODEL_NAME.
"""
import os
from dotenv import load_dotenv

# Cargar .env de la raíz del proyecto (3 niveles arriba de este archivo)
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
load_dotenv(os.path.join(_ROOT, ".env"))


def get_model_name() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3.2")


def flores_enabled(metric: str) -> bool:
    """Activa/desactiva métricas Flores individuales desde .env."""
    key = f"AI_FLORES_{metric.upper()}"
    return os.getenv(key, "1") == "1"


def flores_export_enabled() -> bool:
    return os.getenv("AI_FLORES_EXPORT", "1") == "1"