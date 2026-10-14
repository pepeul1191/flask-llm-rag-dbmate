#!/usr/bin/env python
import os
import sys
import json
import logging
import datetime

from ai.services.vector_store import (
  check_existing_vector_db,
  should_recreate_vector_db,
  create_vector_db
)
from ai.services.ingestion import ingest_puml, split_documents
from ai.services.retrieval import create_retriever, create_chain, create_direct_chain
from ai.services.migration_generator import (
  generate_sql_migrations_with_rag,
  generate_sql_migrations_direct,
  parse_migration_blocks,
  enforce_original_names,
  save_migration_files
)
from ai.services.fallback import generate_direct_migrations
from ai.services.puml_parser import parse_puml_schema
from ai.services.sql_parser import parse_sql_schema
from ai.services.structural_validator import validate_schema
from ai.services.evaluation import compute_structural_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_MODES = ("llm_only", "rag", "rag_validation")


def _build_chain(mode: str, vector_db):
  """Construye la cadena según el modo solicitado."""
  if mode == "llm_only":
    return create_direct_chain()
  retriever = create_retriever(vector_db)
  return create_chain(retriever)


def _generate_migrations(mode: str, chain, db_type: str, puml_file: str) -> str:
  """Genera las migraciones según el modo."""
  if mode == "llm_only":
    return generate_sql_migrations_direct(chain, db_type, puml_file)

  complete = generate_sql_migrations_with_rag(chain, db_type, puml_file)

  refused = (
    "No puedo cumplir" in complete
    or "I cannot fulfill" in complete
    or complete.startswith("Error:")
  )
  if refused:
    print("⚠️ El modelo rechazó generar migraciones. Usando método alternativo...")
    complete = generate_direct_migrations(puml_file, db_type)
  return complete


def _load_vector_db(puml_file: str):
  """Carga o recrea la base vectorial."""
  vector_db = check_existing_vector_db()
  if should_recreate_vector_db(puml_file, vector_db):
    print("🔄 Creando nueva base de datos vectorial...")
    content = ingest_puml(puml_file)
    if not content:
      return None
    chunks = split_documents(content, puml_file)
    vector_db = create_vector_db(chunks, puml_file)
  else:
    print("✅ Usando base de datos vectorial existente.")
  return vector_db


def _validate_structure(puml_file: str, complete_migrations: str, db_type: str):
  """Valida la estructura generada contra el modelo PUML esperado."""
  print("\n" + "=" * 60)
  print("VALIDACIÓN ESTRUCTURAL CONTRA EL MODELO PUML")
  print("=" * 60)

  try:
    expected_schema = parse_puml_schema(puml_file)
  except Exception as e:
    logger.error(f"Error parsing PUML schema: {e}")
    return None, None

  try:
    generated_schema = parse_sql_schema(complete_migrations, db_type)
  except Exception as e:
    logger.error(f"Error parsing generated SQL: {e}")
    return expected_schema, None

  report = validate_schema(expected_schema, generated_schema)
  print(report.summary())

  metrics = compute_structural_metrics(report)
  print("\n" + "-" * 60)
  print("MÉTRICAS ESTRUCTURALES")
  print("-" * 60)
  for key, value in metrics.items():
    print(f"  {key}: {value}")

  return report, metrics


def _persist_reports(puml_basename: str, mode: str, db_type: str,
                     report, metrics, tables_dict) -> None:
  """Guarda el reporte de validación y las métricas en JSON."""
  ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
  base = f"{puml_basename}_{db_type}_{mode}_{ts}"

  if report is not None:
    report_file = f"validation_report_{base}.json"
    with open(report_file, "w", encoding="utf-8") as f:
      json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"✓ Reporte de validación guardado en: {report_file}")

  if metrics is not None:
    metrics_file = f"metrics_{base}.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
      json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"✓ Métricas guardadas en: {metrics_file}")

  if tables_dict:
    dict_file = f"migrations_dict_{base}.json"
    with open(dict_file, "w", encoding="utf-8") as f:
      json.dump({k: v.__dict__ for k, v in tables_dict.items()},
                f, indent=2, ensure_ascii=False)
    print(f"✓ Diccionario de migraciones guardado en: {dict_file}")


def execute(folder_path: str, db_type: str, mode: str = "rag_validation"):
  """
  Orquesta la generación y validación de migraciones SQL desde PUML.

  Args:
    folder_path: carpeta que contiene modelo.puml
    db_type: sqlite | mysql | postgres
    mode: llm_only | rag | rag_validation
  Returns:
    (resultado, exito)
  """
  if mode not in VALID_MODES:
    return f"❌ Modo inválido: {mode}. Use uno de {VALID_MODES}", False

  print(f"DEMO - Generación de migraciones SQL desde PUML (modo={mode})")

  puml_file = os.path.join(folder_path, "modelo.puml")
  if not os.path.exists(puml_file):
    print(f"❌ Archivo PUML no encontrado en {puml_file}")
    return "❌ Archivo no encontrado", False

  # 1. Base vectorial (solo si el modo la requiere)
  vector_db = None
  if mode in ("rag", "rag_validation"):
    vector_db = _load_vector_db(puml_file)

  # 2. Construir cadena
  chain = _build_chain(mode, vector_db)

  # 3. Generar migraciones
  print(f"🔄 Generando migraciones SQL para {puml_file} (db={db_type}, mode={mode})...")
  complete_migrations = _generate_migrations(mode, chain, db_type, puml_file)

  if not complete_migrations or complete_migrations.startswith("Error:"):
    print("❌ No se pudieron generar migraciones.")
    return "❌ No se pudieron generar migraciones.", False

  # 4. Mostrar resultado
  print("\n" + "=" * 60)
  print(f"MIGRACIONES SQL GENERADAS PARA: {puml_file}")
  print("=" * 60)
  print(complete_migrations)

  # 5. Parsear y organizar
  print("\n" + "=" * 60)
  print("ORGANIZANDO EN DICCIONARIO:")
  print("=" * 60)
  tables_dict = parse_migration_blocks(complete_migrations)
  if not tables_dict:
    print("❌ No se pudieron parsear las migraciones.")
    return "❌ No se pudieron parsear las migraciones.", False

  tables_dict = enforce_original_names(puml_file, tables_dict)

  resp = []
  print(f"\n✅ Se procesaron {len(tables_dict)} tablas ÚNICAS:\n")
  for key, table in tables_dict.items():
    print(f"Tabla {key} ({table.table_name}):")
    print(f"  UP:   {table.up}")
    print(f"  DOWN: {table.down}")
    print("-" * 80)
    resp.append(table.__dict__)

  # 6. Validación estructural (solo en rag_validation)
  report = None
  metrics = None
  if mode == "rag_validation":
    report, metrics = _validate_structure(puml_file, complete_migrations, db_type)
    if report is None:
      print("⚠️ No se pudo completar la validación estructural.")
    elif report.is_valid:
      print("✅ Validación estructural: SIN ERRORES detectados.")
    else:
      print("⚠️ Validación estructural: se detectaron diferencias.")

  # 7. Guardar archivos
  puml_basename = os.path.splitext(os.path.basename(puml_file))[0]
  save_migration_files(tables_dict, puml_basename, db_type, complete_migrations)

  _persist_reports(puml_basename, mode, db_type, report, metrics, tables_dict)

  return resp, True


def run_comparison(folder_path: str, db_type: str):
  """
  Ejecuta los tres modos sobre el mismo PUML y compara resultados.
  Útil para responder al Reviewer 1 (LLM vs RAG vs RAG+validación).
  """
  results = {}
  for mode in VALID_MODES:
    print("\n" + "#" * 70)
    print(f"# MODO: {mode}")
    print("#" * 70)
    resp, ok = execute(folder_path, db_type, mode=mode)
    results[mode] = {"success": ok, "tables": len(resp) if ok else 0}

  print("\n" + "=" * 70)
  print("RESUMEN COMPARATIVO")
  print("=" * 70)
  for mode, data in results.items():
    status = "✅" if data["success"] else "❌"
    print(f"  {status} {mode}: {data['tables']} tablas")

  summary_file = f"comparison_{os.path.basename(folder_path)}_{db_type}.json"
  with open(summary_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
  print(f"\n✓ Resumen comparativo guardado en: {summary_file}")
  return results


if __name__ == "__main__":
  if len(sys.argv) < 3:
    print("Uso: python main.py <carpeta_con_puml> <tipo_db> [modo]")
    print("  modo: llm_only | rag | rag_validation | compare")
    sys.exit(1)

  folder = sys.argv[1]
  db = sys.argv[2]
  mode = sys.argv[3] if len(sys.argv) > 3 else "rag_validation"

  if mode == "compare":
    run_comparison(folder, db)
  else:
    execute(folder, db, mode=mode)