#!/usr/bin/env python
import os
import sys
import json
import time
import logging
import datetime
import inspect
from ai import env

from ai.paths import output_base, under_output
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

# 🔧 CAMBIO: máximo de iteraciones del bucle de corrección en rag_validation.
# Configurable por env var AI_MAX_CORRECTION_ITERS (default 3, igual que el paper).
MAX_CORRECTION_ITERATIONS = int(os.getenv("AI_MAX_CORRECTION_ITERS", "3"))

# 🔧 CAMBIO: detecta si migration_generator.py soporta feedback de errores.
# Si no lo soporta, rag_validation degrada a una sola pasada (y lo avisa).
_HAS_EXTRA_INSTRUCTIONS = (
  "extra_instructions" in inspect.signature(
    generate_sql_migrations_with_rag
  ).parameters
)

_AI_TIMING = os.getenv("AI_TIMING", "0") == "1"


def _timed(label, fn, *args, **kwargs):
  if not _AI_TIMING:
    return fn(*args, **kwargs)
  t0 = time.perf_counter()
  try:
    return fn(*args, **kwargs)
  finally:
    print(f"⏱ [timing] {label}: {time.perf_counter()-t0:.3f}s")


def _build_chain(mode: str, vector_db, puml_file: str):
  if mode == "llm_only":
    return create_direct_chain()
  retriever = create_retriever(vector_db, source_file=puml_file)
  return create_chain(retriever)


def _generate_migrations(mode: str, chain, db_type: str, puml_file: str) -> str:
  """Genera las migraciones según el modo (una sola pasada, sin corrección)."""
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


# 🔧 CAMBIO: bucle de generación + validación + corrección (modo rag_validation).
def _generate_with_correction(chain, db_type: str, puml_file: str,
                              max_iter: int = MAX_CORRECTION_ITERATIONS):
  """
  Genera migraciones con bucle de corrección (modo rag_validation).

  Flujo:
    1. Genera SQL con RAG (igual que el modo 'rag').
    2. Valida contra el PUML.
    3. Si hay errores y quedan iteraciones, re-invoca al LLM pasándole el
       reporte de errores como 'extra_instructions' y vuelve a validar.
    4. Devuelve (sql_final, n_iter, report_final, metrics_final).

  Si migration_generator.py no acepta 'extra_instructions', se ejecuta
  una sola pasada (equivalente a 'rag') y se emite un warning.
  """
  # Primera pasada (idéntica a 'rag')
  sql = _generate_migrations("rag", chain, db_type, puml_file)
  if not sql or sql.startswith("Error:"):
    return sql, 0, None, None

  report, metrics = None, None

  for i in range(max_iter):
    try:
      # Validación silenciosa: no imprime la tabla grande en cada iteración
      report, metrics = _validate_structure(
        puml_file, sql, db_type, verbose=False
      )
    except Exception as e:
      logger.error(f"Error validando iteración {i}: {e}")
      return sql, i, None, None

    # Éxito: no hay nada que corregir
    if report is None or report.is_valid:
      if i > 0:
        print(f"✅ Validación OK tras {i} iteración(es) de corrección")
      return sql, i, report, metrics

    # ¿Podemos pasar feedback al LLM?
    if not _HAS_EXTRA_INSTRUCTIONS:
      logger.warning(
        "generate_sql_migrations_with_rag no acepta 'extra_instructions'. "
        "El bucle de corrección queda desactivado para este run "
        "(actualiza migration_generator.py para habilitarlo)."
      )
      return sql, i, report, metrics

    # Reportar errores y re-generar
    n_missing_tables = len(report.missing_tables)
    n_missing_cols = sum(len(v) for v in report.missing_columns.values())
    n_type = sum(len(v) for v in report.type_mismatches.values())
    n_pk = len(report.pk_mismatches)
    n_fk = len(report.fk_mismatches)
    print(
      f"🔄 Corrección {i+1}/{max_iter}: "
      f"{n_missing_tables} tablas, {n_missing_cols} cols, "
      f"{n_type} tipos, {n_pk} PKs, {n_fk} FKs"
    )

    sql = generate_sql_migrations_with_rag(
      chain, db_type, puml_file,
      extra_instructions=report.summary(),
    )
    if not sql or sql.startswith("Error:"):
      return sql, i + 1, report, metrics

  # Agotamos las iteraciones sin converger: devolver el último estado
  try:
    report, metrics = _validate_structure(puml_file, sql, db_type, verbose=False)
  except Exception as e:
    logger.error(f"Error en validación final: {e}")

  if report is not None and not report.is_valid:
    print(f"⚠️ No convergió en {max_iter} iteraciones (quedan errores)")

  return sql, max_iter, report, metrics


def _load_vector_db(puml_file: str):
  vector_db = check_existing_vector_db()
  if should_recreate_vector_db(puml_file, vector_db):
    print("🔄 Creando nueva base de datos vectorial...")
    content = ingest_puml(puml_file)
    if not content:
      return None
    chunks = split_documents(content, puml_file)
    vector_db = create_vector_db(chunks, puml_file)
    print(f"✅ Vector DB recreada con {len(chunks)} chunks.")
  else:
    print("✅ Usando base de datos vectorial existente.")
  return vector_db


# 🔧 CAMBIO: parámetro 'verbose' para no spamear en el bucle de corrección.
def _validate_structure(puml_file: str, complete_migrations: str, db_type: str,
                        verbose: bool = True):
  """Valida la estructura generada contra el modelo PUML esperado."""
  if verbose:
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

  if verbose:
    print(report.summary())

  metrics = compute_structural_metrics(report)

  if verbose:
    print("\n" + "-" * 60)
    print("MÉTRICAS ESTRUCTURALES")
    print("-" * 60)
    for key, value in metrics.items():
      print(f"  {key}: {value}")

  return report, metrics


# 🔧 CAMBIO: parámetro 'correction_iters' para persistirlo en metrics_*.json.
def _persist_reports(puml_basename: str, mode: str, db_type: str,
                     report, metrics, tables_dict,
                     correction_iters: int = 0) -> None:
  """Guarda el reporte de validación y las métricas en JSON dentro de tmp/."""
  run_id = os.getenv("AI_RUN_ID")
  if run_id:
    base = f"{run_id}_{puml_basename}_{db_type}_{mode}"
  else:
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    base = f"{puml_basename}_{db_type}_{mode}_{ts}"

  # Añadir iteraciones de corrección a las métricas (útil para el paper)
  if metrics is not None and correction_iters is not None:
    metrics = dict(metrics)
    metrics["correction_iterations"] = correction_iters

  if report is not None:
    report_file = under_output(f"validation_report_{base}.json")
    with open(report_file, "w", encoding="utf-8") as f:
      json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"✓ Reporte de validación guardado en: {report_file}")

  if metrics is not None:
    metrics_file = under_output(f"metrics_{base}.json")
    with open(metrics_file, "w", encoding="utf-8") as f:
      json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"✓ Métricas guardadas en: {metrics_file}")

  if tables_dict:
    dict_file = under_output(f"migrations_dict_{base}.json")
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
  chain = _build_chain(mode, vector_db, puml_file)

  # 3. Generar migraciones
  print(f"🔄 Generando migraciones SQL para {puml_file} (db={db_type}, mode={mode})...")

  # 🔧 CAMBIO: rama con/sin bucle de corrección
  correction_iters = 0
  report = None
  metrics = None

  if mode == "rag_validation":
    complete_migrations, correction_iters, report, metrics = _timed(
      "llm_generation_with_correction",
      _generate_with_correction, chain, db_type, puml_file
    )
    print(f"✓ Generación con corrección completada en {correction_iters} iteración(es)")
  else:
    complete_migrations = _timed(
      "llm_generation",
      _generate_migrations, mode, chain, db_type, puml_file
    )

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

  # 6. Validación estructural final para el reporte
  #    - rag_validation: ya viene del bucle -> no repetir
  #    - llm_only / rag: validar ahora
  if report is None:
    report, metrics = _timed(
      "structural_validation",
      _validate_structure, puml_file, complete_migrations, db_type
    )

  if report is None:
    print("⚠️ No se pudo completar la validación estructural.")
  elif report.is_valid:
    print("✅ Validación estructural: SIN ERRORES detectados.")
  else:
    print("⚠️ Validación estructural: se detectaron diferencias.")

  # 7. Guardar archivos
  puml_basename = os.getenv("AI_PUML_BASENAME") or \
                os.path.splitext(os.path.basename(puml_file))[0]
  save_migration_files(tables_dict, puml_basename, db_type, complete_migrations)

  _persist_reports(
    puml_basename, mode, db_type, report, metrics, tables_dict,
    correction_iters=correction_iters,
  )

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
    print("Uso: python -m ai.main <carpeta_o_puml> <tipo_db> [modo]")
    print("  modo: llm_only | rag | rag_validation | compare | errors | pipeline")
    sys.exit(1)

  folder = sys.argv[1]
  db = sys.argv[2]
  mode = sys.argv[3] if len(sys.argv) > 3 else "rag_validation"

  if mode == "compare":
    run_comparison(folder, db)
  elif mode == "errors":
    from ai.pipeline import run_structural_validation_tests
    result = run_structural_validation_tests(folder, db)
    print("\n" + "=" * 60)
    print("RESULTADO DE TESTS DE VALIDACIÓN ESTRUCTURAL")
    print("=" * 60)
    print("Aggregate:", result["aggregate"])
    for etype, m in result["per_error_type"].items():
      print(f"  {etype}: {m}")
  elif mode == "pipeline":
    from ai.pipeline import run_from_config
    cfg_path = sys.argv[4] if len(sys.argv) > 4 else "pipeline_config.json"
    run_from_config(cfg_path)
  else:
    execute(folder, db, mode=mode)