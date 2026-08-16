# ai/services/ingestion.py
import os
import re
import logging
from langchain_core.documents import Document
from .vector_store import get_puml_file_hash

logger = logging.getLogger(__name__)


def ingest_puml(puml_path: str) -> str | None:
  """Lee el contenido del archivo PUML."""
  if os.path.exists(puml_path):
    with open(puml_path, 'r', encoding='utf-8') as f:
      content = f.read()
    logger.info("PUML file loaded successfully.")
    return content
  else:
    logger.error(f"PUML file not found at path: {puml_path}")
    return None


def split_documents(content: str, puml_path: str):
  """Divide el contenido PUML en fragmentos semánticos (entidades, relaciones, líneas)."""
  file_hash = hash(content)
  chunks = []

  # 1. Entidades
  entity_pattern = r'(entity\s+\w+\s*\{[^}]+\})'
  entities = re.findall(entity_pattern, content, re.IGNORECASE | re.DOTALL)
  if entities:
    logger.info(f"Found {len(entities)} entities using entity pattern")
    for i, entity in enumerate(entities):
      chunks.append(Document(
        page_content=entity,
        metadata={
          "source": "puml_file",
          "chunk_id": len(chunks),
          "chunk_type": "entity",
          "source_file": puml_path,
          "source_file_hash": file_hash
        }
      ))

  # 2. Relaciones
  relationship_pattern = r'(\w+\s+--\s+\w+|"\w+"\s+--\s+"\w+")'
  relationships = re.findall(relationship_pattern, content)
  if relationships:
    logger.info(f"Found {len(relationships)} relationships")
    relationship_chunk = "Relationships:\n" + "\n".join(relationships)
    chunks.append(Document(
      page_content=relationship_chunk,
      metadata={
        "source": "puml_file",
        "chunk_id": len(chunks),
        "chunk_type": "relationships",
        "source_file": puml_path,
        "source_file_hash": file_hash
      }
    ))

  # 3. Fallback: dividir por líneas
  if not chunks:
    logger.info("Using line-based chunking as fallback")
    lines = content.splitlines()
    chunk_size = 15
    for i in range(0, len(lines), chunk_size):
      chunk_lines = lines[i:i + chunk_size]
      chunk_text = "\n".join(chunk_lines)
      chunks.append(Document(
        page_content=chunk_text,
        metadata={
          "source": "puml_file",
          "chunk_id": len(chunks),
          "chunk_type": "line_chunk",
          "source_file": puml_path,
          "source_file_hash": file_hash
        }
      ))

  logger.info(f"PUML content split into {len(chunks)} chunks.")
  return chunks