#!/usr/bin/env python
import os
import sys
import logging
import json

from ai.services.vector_store import check_existing_vector_db, should_recreate_vector_db
from ai.services.ingestion import ingest_puml, split_documents
from ai.services.vector_store import create_vector_db
from ai.services.retrieval import create_retriever, create_chain
from ai.services.migration_generator import (
  generate_sql_migrations_with_rag,
  parse_migration_blocks,
  validate_entity_count,
  enforce_original_names,
  save_migration_files
)
from ai.services.fallback import generate_direct_migrations

logging.basicConfig(level=logging.INFO)


def execute(folder_path: str, db_type: str):
  """Función principal que orquesta la generación de migraciones."""
  print('DEMO - Generación de migraciones SQL desde PUML')

  puml_file = os.path.join(folder_path, "modelo.puml")
  if not os.path.exists(puml_file):
    print(f"❌ Archivo PUML no encontrado en {puml_file}")
    return "❌ Archivo no encontrado", False

  # 1. Base vectorial
  vector_db = check_existing_vector_db()
  if should_recreate_vector_db(puml_file, vector_db):
    print("🔄 Creando nueva base de datos vectorial...")
    content = ingest_puml(puml_file)
    if not content:
      return "❌ No se pudo leer el PUML.", False
    chunks = split_documents(content, puml_file)
    vector_db = create_vector_db(chunks, puml_file)
  else:
    print("✅ Usando base de datos vectorial existente.")

  # 2. Crear retriever y cadena
  retriever = create_retriever(vector_db)
  chain = create_chain(retriever)

  # 3. Generar migraciones
  print(f"🔄 Generando migraciones SQL para {puml_file}...")
  complete_migrations = generate_sql_migrations_with_rag(chain, db_type, puml_file)

  # Fallback si el modelo rechaza
  if "No puedo cumplir" in complete_migrations or "I cannot fulfill" in complete_migrations or complete_migrations.startswith("Error:"):
    print("⚠️ El modelo rechazó generar migraciones. Usando método alternativo...")
    complete_migrations = generate_direct_migrations(puml_file, db_type)

  if not complete_migrations or "Error:" in complete_migrations:
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

  validate_entity_count(puml_file, tables_dict)
  tables_dict = enforce_original_names(puml_file, tables_dict)

  resp = []
  if tables_dict:
    print(f"\n✅ Se procesaron {len(tables_dict)} tablas ÚNICAS:\n")
    for key, table in tables_dict.items():
      print(f"Tabla {key} ({table.table_name}):")
      print(f"  UP:   {table.up}")
      print(f"  DOWN: {table.down}")
      print("-" * 80)
      resp.append(table.__dict__)
  else:
    print("❌ No se pudieron procesar las migraciones.")
    return "❌ No se pudieron procesar las migraciones.", False

  # 6. Guardar archivos
  #save = input("\n¿Guardar las migraciones en archivos? (s/n): ").strip().lower()
  #if save == 's':
  puml_basename = os.path.splitext(os.path.basename(puml_file))[0]
  save_migration_files(tables_dict, puml_basename, db_type, complete_migrations)

  #save_json = input("¿Guardar diccionario como JSON? (s/n): ").strip().lower()
  #if save_json == 's':
  json_filename = f"migrations_dict_{puml_basename}_{db_type}.json"
  with open(json_filename, 'w', encoding='utf-8') as f:
    json.dump({k: v.__dict__ for k, v in tables_dict.items()}, f, indent=2, ensure_ascii=False)
  print(f"✓ Diccionario guardado en: {json_filename}")

  return resp, True

"""
if __name__ == "__main__":
  if len(sys.argv) < 3:
    print("Uso: python main.py <carpeta_con_puml> <tipo_db>")
    sys.exit(1)
  folder = sys.argv[1]
  db = sys.argv[2]
  demo(folder, db)
"""