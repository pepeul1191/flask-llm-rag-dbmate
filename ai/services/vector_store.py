# ai/services/vector_store.py
import os
import json
import shutil
import hashlib
import logging
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

EMBEDDING_MODEL = "nomic-embed-text"
VECTOR_STORE_NAME = "puml-rag"
PERSIST_DIRECTORY = "./chroma_db"
META_FILE = os.path.join(PERSIST_DIRECTORY, "meta.json")

from ai.paths import output_base
import os

PERSIST_DIRECTORY = os.path.join(output_base(), "chroma_db")
META_FILE = os.path.join(PERSIST_DIRECTORY, "meta.json")

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Hash determinista del PUML
# ---------------------------------------------------------------------------
def get_puml_file_hash(puml_path: str) -> str | None:
  """
  SHA-256 del contenido del PUML. Determinista entre procesos
  (a diferencia de hash() que usa PYTHONHASHSEED aleatorio).
  """
  if not os.path.exists(puml_path):
    return None
  with open(puml_path, 'rb') as f:
    return hashlib.sha256(f.read()).hexdigest()


# ---------------------------------------------------------------------------
# Metadata persistida (archivo + hash del último ingest)
# ---------------------------------------------------------------------------
def _read_meta() -> dict:
  if os.path.exists(META_FILE):
    try:
      with open(META_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
      return {}
  return {}


def _write_meta(data: dict) -> None:
  os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
  with open(META_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Decisión de recrear
# ---------------------------------------------------------------------------
def should_recreate_vector_db(puml_file: str, vector_db) -> bool:
  """
  Recrea si:
    - no hay DB,
    - el hash del PUML cambió,
    - cambió la ruta del PUML,
    - la metadata no existe (DB creada por versión antigua).
  """
  if vector_db is None:
    logger.info("No vector DB found -> recreate.")
    return True

  current_hash = get_puml_file_hash(puml_file)
  if current_hash is None:
    logger.warning("PUML no encontrado al calcular hash.")
    return True

  meta = _read_meta()
  stored_hash = meta.get("source_file_hash")
  stored_file = meta.get("source_file")

  if stored_hash is None:
    logger.info("No metadata found -> recreate (old DB).")
    return True

  if stored_hash != current_hash:
    logger.info(
      "PUML changed (hash %s -> %s) -> recreate.",
      stored_hash[:8], current_hash[:8]
    )
    return True

  if stored_file and os.path.abspath(stored_file) != os.path.abspath(puml_file):
    logger.info(
      "Different PUML file (%s -> %s) -> recreate.",
      stored_file, puml_file
    )
    return True

  logger.info("Vector DB is up-to-date (hash %s).", current_hash[:8])
  return False


# ---------------------------------------------------------------------------
# Limpieza
# ---------------------------------------------------------------------------
def clear_vector_db() -> bool:
  """Elimina el directorio de la base vectorial de forma segura."""
  if not os.path.exists(PERSIST_DIRECTORY):
    return True
  try:
    shutil.rmtree(PERSIST_DIRECTORY)
    logger.info("Cleared existing vector database.")
    return True
  except Exception as e:
    logger.error("Error clearing vector DB: %s", e)
    try:
      import subprocess
      subprocess.run(['rm', '-rf', PERSIST_DIRECTORY], check=True)
      logger.info("Cleared vector database using alternative method.")
      return True
    except Exception as e2:
      logger.error("Failed to clear vector database: %s", e2)
      return False


# ---------------------------------------------------------------------------
# Carga / creación
# ---------------------------------------------------------------------------
def check_existing_vector_db():
  """Carga la base vectorial existente si existe y tiene documentos."""
  if not os.path.exists(PERSIST_DIRECTORY):
    return None
  try:
    vector_db = Chroma(
      persist_directory=PERSIST_DIRECTORY,
      embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
      collection_name=VECTOR_STORE_NAME
    )
    count = vector_db._collection.count()
    if count > 0:
      logger.info("Found existing vector database with %d documents.", count)
      return vector_db
    logger.info("Existing vector DB is empty.")
  except Exception as e:
    logger.warning("Existing DB issue: %s", e)
  return None


def create_vector_db(chunks, puml_path: str):
  """
  Crea la base vectorial desde cero.
  SIEMPRE limpia el directorio antes para evitar mezclar PUMLs.
  """
  logger.info("Recreating vector DB from scratch (%d chunks).", len(chunks))

  # Borrado total para no arrastrar embeddings viejos
  if not clear_vector_db():
    logger.error("No se pudo limpiar la DB. Abortando para evitar mezcla.")
    raise RuntimeError("No se pudo limpiar chroma_db")

  embedding = OllamaEmbeddings(model=EMBEDDING_MODEL)

  try:
    os.makedirs(PERSIST_DIRECTORY, exist_ok=True, mode=0o755)
    vector_db = Chroma.from_documents(
      documents=chunks,
      embedding=embedding,
      collection_name=VECTOR_STORE_NAME,
      persist_directory=PERSIST_DIRECTORY
    )
    vector_db.persist()

    # Verificación de conteo
    count = vector_db._collection.count()
    if count != len(chunks):
      logger.warning(
        "Chunks esperados=%d, persistidos=%d", len(chunks), count
      )

    # Guardar metadata con el hash del PUML
    _write_meta({
      "source_file": os.path.abspath(puml_path),
      "source_file_hash": get_puml_file_hash(puml_path),
      "chunk_count": count,
    })

    logger.info("Vector DB created for %s (%d chunks).", puml_path, count)
    return vector_db

  except Exception as e:
    logger.error("Error creating persistent vector DB: %s", e)
    # Fallback en memoria (no persiste, evita el problema de mezcla)
    return Chroma.from_documents(
      documents=chunks,
      embedding=embedding,
      collection_name=VECTOR_STORE_NAME
    )


def load_vector_db():
  """Carga la base vectorial desde disco."""
  try:
    return Chroma(
      persist_directory=PERSIST_DIRECTORY,
      embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
      collection_name=VECTOR_STORE_NAME
    )
  except Exception as e:
    logger.error("Error loading vector DB: %s", e)
    return None