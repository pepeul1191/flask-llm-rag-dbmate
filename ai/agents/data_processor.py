# application/ai/agents/data_processor.py
import re
import logging
from langchain_core.documents import Document

class DataProcessor:
  """Agente especializado en procesamiento de datos PUML"""
  
  @staticmethod
  def split_puml_content(content, puml_path):
    """Divide el contenido PUML en chunks manejables"""
    file_hash = hash(content)
    chunks = []
    
    entity_pattern = r'(entity\s+\w+\s*\{[^}]+\})'
    entities = re.findall(entity_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if entities:
      logging.info(f"Found {len(entities)} entities using entity pattern")
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
    
    relationship_pattern = r'(\w+\s+--\s+\w+|"\w+"\s+--\s+"\w+")'
    relationships = re.findall(relationship_pattern, content)
    
    if relationships:
      logging.info(f"Found {len(relationships)} relationships")
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
    
    if not chunks:
      logging.info("Using line-based chunking as fallback")
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
    
    logging.info(f"PUML content split into {len(chunks)} chunks.")
    return chunks
  
  @staticmethod
  def extract_entities_info(puml_content):
    """Extrae información estructurada de las entidades PUML"""
    entity_pattern = r'entity\s+(\w+)\s*\{([^}]+)\}'
    entities = re.findall(entity_pattern, puml_content, re.IGNORECASE | re.DOTALL)
    
    entity_info = []
    for entity_name, entity_content in entities:
      attributes = re.findall(r'\s*(\w+)\s*:\s*([^\n]+)', entity_content)
      entity_info.append({
        'name': entity_name,
        'attributes': attributes,
        'raw_content': entity_content
      })
    
    return entity_info
  
  @staticmethod
  def count_entities(puml_content):
    """Cuenta las entidades en el contenido PUML"""
    entity_pattern = r'entity\s+(\w+)'
    entities = re.findall(entity_pattern, puml_content, re.IGNORECASE)
    return len(entities)