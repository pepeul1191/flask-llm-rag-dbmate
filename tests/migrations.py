import os
import datetime
import subprocess
import traceback

def execute_migrations(project, migrations):
  # Crear timestamp actual
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  
  # Obtener la ruta del directorio actual del proyecto
  project_root = os.getcwd()
  
  # Crear ruta de la carpeta en la raíz del proyecto
  folder_path = os.path.join(project_root, "tmp", f"migrations_{timestamp}")

  try:
    # Crear la carpeta
    os.makedirs(folder_path, exist_ok=True)
    print(f"Carpeta creada: {folder_path}")
    
    # archivo .env
    env_path = os.path.join(folder_path, '.env')
    with open(env_path, "w") as archivo:
      archivo.write('DATABASE_URL=' + project['connection_string'])

    # archivos de migraciones
    for migration in migrations:
      text = '-- migrate:up \n\n' + migration['up']
      text = text + '\n\n-- migrate:down \n\n' + migration['down']
      file_path = os.path.join(folder_path, migration['name'] + '.sql')

      with open(file_path, "w") as archivo:
        archivo.write(text)

    # Ejecutar dbmate up especificando el directorio de migraciones
    print(f"Ejecutando dbmate up en: {folder_path}")
    result = subprocess.run(
      ['dbmate', '--migrations-dir', folder_path, 'up'],
      capture_output=True,
      text=True,
      check=True,
      env={**os.environ, 'DATABASE_URL': project['connection_string']}
    )
    
    print("dbmate output:", result.stdout)
    if result.stderr:
      print("dbmate errors:", result.stderr)

    return {
      "data": None,
      "message": "Migraciones generadas y ejecutadas correctamente",
      "success": True,
      "error": None
    }, 200
    
  except subprocess.CalledProcessError as e:
    print(f"Error al ejecutar dbmate: {e}")
    print("stdout:", e.stdout)
    print("stderr:", e.stderr)
    return {
      "data": None,
      "message": f"Error al ejecutar migraciones: {e.stderr}",
      "success": False,
      "error": str(e)
    }, 500
    
  except Exception as e:
    print(f"Error al crear archivo: {str(e)}")
    tb = traceback.format_exc()
    return {
      "data": None,
      "message": f"Error al generar migraciones: {str(e)}",
      "success": False,
      "error": tb
    }, 500