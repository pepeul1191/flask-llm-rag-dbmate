# ai/paths.py
import os

DEFAULT_OUTPUT_DIR = "./tmp"


def output_base() -> str:
    """
    Devuelve el directorio base donde se escriben todos los artefactos.
    Se controla con la variable de entorno APP_OUTPUT_DIR.
    Por defecto: ./tmp (relativo al cwd desde donde se ejecuta).
    """
    base = os.environ.get("APP_OUTPUT_DIR", DEFAULT_OUTPUT_DIR)
    os.makedirs(base, exist_ok=True)
    return base


def under_output(*parts: str) -> str:
    """Une el base con los fragmentos dados, creando la carpeta si hace falta."""
    path = os.path.join(output_base(), *parts)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path