# ai/services/__init__.py
from .vector_store import (
  check_existing_vector_db,
  should_recreate_vector_db,
  create_vector_db,
  load_vector_db,
  clear_vector_db,
  get_puml_file_hash
)
from .ingestion import ingest_puml, split_documents
from .retrieval import create_retriever, create_chain, create_direct_chain
from .migration_generator import (
  generate_sql_migrations_with_rag,
  generate_sql_migrations_direct,
  parse_migration_blocks,
  validate_entity_count,
  enforce_original_names,
  save_migration_files,
  extract_table_name
)
from .fallback import generate_direct_migrations, map_puml_to_sql
from .puml_parser import parse_puml_schema
from .sql_parser import parse_sql_schema
from .structural_validator import validate_schema, ValidationReport
from .evaluation import compute_structural_metrics, inject_errors

__all__ = [
  # vector store
  "check_existing_vector_db",
  "should_recreate_vector_db",
  "create_vector_db",
  "load_vector_db",
  "clear_vector_db",
  "get_puml_file_hash",
  # ingestion
  "ingest_puml",
  "split_documents",
  # retrieval
  "create_retriever",
  "create_chain",
  "create_direct_chain",
  # migration generator
  "generate_sql_migrations_with_rag",
  "generate_sql_migrations_direct",
  "parse_migration_blocks",
  "validate_entity_count",
  "enforce_original_names",
  "save_migration_files",
  "extract_table_name",
  # fallback
  "generate_direct_migrations",
  "map_puml_to_sql",
  # nuevos
  "parse_puml_schema",
  "parse_sql_schema",
  "validate_schema",
  "ValidationReport",
  "compute_structural_metrics",
  "inject_errors",
]