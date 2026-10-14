# ai/services/ingestion.py
import os
import re
import hashlib
import logging
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def ingest_puml(puml_path: str) -> str | None:
  """Lee el contenido del archivo PUML."""
  if os.path.exists(puml_path):
    with open(puml_path, 'r', encoding='utf-8') as f:
      content = f.read()
    logger.info("PUML file loaded successfully.")
    return content
  logger.error("PUML file not found at path: %s", puml_path)
  return None


def split_documents(content: str, puml_path: str):
  """
  Divide el contenido PUML en fragmentos semánticos.
  Usa SHA-256 (determinista) para que el hash coincida con vector_store.
  """
  file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
  chunks = []

  # 1. Entidades
  entity_pattern = r'(entity\s+\w+\s*\{[^}]+\})'
  entities = re.findall(entity_pattern, content, re.IGNORECASE | re.DOTALL)
  if entities:
    logger.info("Found %d entities.", len(entities))
    for entity in entities:
      chunks.append(Document(
        page_content=entity,
        metadata={
          "source": "puml_file",
          "chunk_id": len(chunks),
          "chunk_type": "entity",
          "source_file": os.path.abspath(puml_path),
          "source_file_hash": file_hash
        }
      ))

  # 2. Relaciones
  relationship_pattern = r'(\w+\s+--\s+\w+|"\w+"\s+--\s+"\w+")'
  relationships = re.findall(relationship_pattern, content)
  if relationships:
    logger.info("Found %d relationships.", len(relationships))
    relationship_chunk = "Relationships:\n" + "\n".join(relationships)
    chunks.append(Document(
      page_content=relationship_chunk,
      metadata={
        "source": "puml_file",
        "chunk_id": len(chunks),
        "chunk_type": "relationships",
        "source_file": os.path.abspath(puml_path),
        "source_file_hash": file_hash
      }
    ))

  # 3. Fallback: dividir por líneas
  if not chunks:
    logger.info("Using line-based chunking as fallback.")
    lines = content.splitlines()
    chunk_size = 15
    for i in range(0, len(lines), chunk_size):
      chunk_text = "\n".join(lines[i:i + chunk_size])
      chunks.append(Document(
        page_content=chunk_text,
        metadata={
          "source": "puml_file",
          "chunk_id": len(chunks),
          "chunk_type": "line_chunk",
          "source_file": os.path.abspath(puml_path),
          "source_file_hash": file_hash
        }
      ))

  logger.info("PUML content split into %d chunks.", len(chunks))
  return chunks