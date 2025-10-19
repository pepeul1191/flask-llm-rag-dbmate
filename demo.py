# demo.py (archivo principal actualizado)
import os
import datetime
import json
from ai.rag_services import RAGServices
from ai.migration_generator import MigrationGenerator

def save_migration_files(tables_dict, puml_basename, db_type, complete_migrations):
  """Guarda archivos de migración"""
  if not tables_dict:
    print("❌ No hay migraciones para guardar.")
    return
  
  complete_filename = f"complete_migrations_{puml_basename}_{db_type}.sql"
  with open(complete_filename, 'w', encoding='utf-8') as f:
    f.write(f"-- Migraciones generadas desde: {puml_basename}.puml\n")
    f.write(f"-- Tipo de base de datos: {db_type}\n")
    f.write(f"-- Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"-- Total de tablas: {len(tables_dict)}\n\n")
    f.write(complete_migrations)
  print(f"✓ Migraciones completas guardadas en: {complete_filename}")
  
  migrations_dir = f"migrations_{puml_basename}_{db_type}"
  if os.path.exists(migrations_dir):
    import shutil
    shutil.rmtree(migrations_dir)
  os.makedirs(migrations_dir, exist_ok=True)
  
  base_timestamp = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
  saved_count = 0

  for key, table_data in tables_dict.items():
    table_name = table_data.get('table_name')
    if table_name:
      timestamp = str(base_timestamp + key)
      migration_filename = f"{migrations_dir}/{timestamp}_create_{table_name}.sql"

      with open(migration_filename, 'w', encoding='utf-8') as f:
        f.write(table_data['complete_block'])
      
      saved_count += 1
      print(f"✓ Migración {key} ({table_name}) guardada en: {migration_filename}")

  print(f"✓ Total de archivos guardados: {saved_count}")

def main():
  db_type = input("Tipo de base de datos (sqlite, mysql, postgres): ").strip().lower()
  if db_type not in ['sqlite', 'mysql', 'postgres']:
    print("Tipo de base de datos no válido.")
    return

  puml_file = input("Ruta al archivo PUML (presiona Enter para usar 'schema.puml'): ").strip()
  
  if not puml_file:
    puml_file = "schema.puml"
  
  if not os.path.exists(puml_file):
    print(f"El archivo PUML no existe en la ruta {puml_file}.")
    return

  vector_db = RAGServices.check_existing_vector_db()
  
  if RAGServices.should_recreate_vector_db(puml_file, vector_db):
    print("Creando nueva base de datos vectorial RAG...")
    vector_db = RAGServices.create_vector_db_from_puml(puml_file)
  else:
    print("Usando base de datos vectorial RAG existente.")

  migration_generator = MigrationGenerator(vector_db)
  
  print(f"Generando migraciones SQL para {puml_file} usando RAG...")
  
  complete_migrations = migration_generator.generate_sql_migrations_with_rag(db_type, puml_file)
  
  result = migration_generator.process_migrations(complete_migrations, puml_file, db_type)
  
  if result:
    tables_dict = result['tables_dict']
    complete_migrations = result['complete_migrations']
    
    print(f"\n✅ RAG generó {len(tables_dict)} tablas:")
    for key, table_data in tables_dict.items():
      print(f"Tabla {key}: {table_data['table_name']}")
    
    save_file = input("\n¿Guardar las migraciones en archivos? (s/n): ").strip().lower()
    if save_file == 's':
      puml_basename = os.path.splitext(os.path.basename(puml_file))[0]
      save_migration_files(tables_dict, puml_basename, db_type, complete_migrations)

      save_json = input("¿Guardar diccionario como JSON? (s/n): ").strip().lower()
      if save_json == 's':
        json_filename = f"migrations_dict_{puml_basename}_{db_type}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
          json.dump(tables_dict, f, indent=2, ensure_ascii=False)
        print(f"✓ Diccionario guardado en: {json_filename}")

if __name__ == "__main__":
  main()