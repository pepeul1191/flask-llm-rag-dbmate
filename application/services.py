# services/engine_service.py
import traceback
import subprocess
import os
import time
from datetime import datetime
from plantuml import PlantUML  
from application.models import Engine, Project
from sqlalchemy import text
from pathlib import Path
from sqlalchemy.orm import joinedload
from main.database import session
from ai.draft import demo

def build_response(data=None, message="Operación exitosa", success=True):
  return {
    "data": data,
    "message": message,
    "success": success,
    "error": None
  }

def handle_error(message, traceback=None):
  # Aquí podrías registrar logs si es necesario
  print(message)
  if traceback:
    print(traceback)
  return {
    "error": traceback,
    "message": message,
    "data": None,
    "success": False
  }

# ++++++++++++++++++++++++++++++++++++++++++++++++++++ 
# engines
# ++++++++++++++++++++++++++++++++++++++++++++++++++++

def fetch_engines():
  try:
    # Usar context manager para manejo de sesión
    engines = session.query(Engine).all()
    data = [
      {
        "id": engine.id,
        "name": engine.name,
        "image": engine.image
      }
      for engine in engines
    ]
    message = (
      f"Se encontraron {len(data)} motores de bases de datos" 
      if data else 
      "No hay motores de bases de datos configurados"
    )
    return build_response(
      success=True,
      data=data,
      message=message
    )
  except Exception as e:
    print(f"Error inesperado: {str(e)}")
    return build_response(
      success=False,
      data=[],
      message="Error del servicio",
      error={"message": "Error interno del servidor"}
    )
  
# ++++++++++++++++++++++++++++++++++++++++++++++++++++ 
# projects
# ++++++++++++++++++++++++++++++++++++++++++++++++++++
  
def fetch_project(project_id):
  try:
    project = session.query(Project)\
      .options(
        joinedload(Project.engine),
        joinedload(Project.migrations)
      )\
      .filter(Project.id == project_id)\
      .first()
    
    if not project:
      return build_response(success=False, message="Proyecto no encontrado"), 400
    
    project_data = {
      "id": project.id,
      "connection_string": project.connection_string,
      "description": project.description,
      "title": project.title,
      "engine": {
        "id": project.engine.id,
        "image": project.engine.image,
        "name": project.engine.name
      },
      "migrations": [
        {
          "id": migration.id,
          "name": migration.name,
          "timestamp": migration.timestamp,
          "up": migration.up,
          "executed": migration.executed,
          "created": migration.created_at.strftime("%Y-%m-%d %H:%M:%S") if migration.created_at else None
        }
        for migration in project.migrations
      ]
    }
    
    return build_response(data=project_data, message="Proyecto obtenido exitosamente"), 200
  except Exception as e:
    tb = traceback.format_exc()
    return handle_error(f"Error al obtener proyecto: {str(e)}", tb)

def fetch_projects():
  try:
    projects = session.query(Project)\
      .options(
        joinedload(Project.engine),
        joinedload(Project.migrations)
      )\
      .all()
    
    result = []
    for project in projects:
      project_data = {
        "id": project.id,
        "connection_string": project.connection_string,
        "description": project.description,
        "title": project.title,
        "engine": {
          "id": project.engine.id,
          "image": project.engine.image,
          "name": project.engine.name
        },
        "migrations": [
          {
            "id": migration.id,
            "name": migration.name,
            "timestamp": migration.timestamp,
            "up": migration.up,
            "executed": migration.executed,
            "created": migration.created_at.strftime("%Y-%m-%d %H:%M:%S") if migration.created_at else None
          }
          for migration in project.migrations
        ]
      }
      
      result.append(project_data)
    
    return build_response(data=result, message="Lista de proyectos obtenida exitosamente"), 200

  except Exception as e:
    tb = traceback.format_exc()
    return handle_error(f"Error al obtener proyectos: {str(e)}", tb)

def create_project(data):
  try:
    title = data.get('title')
    description = data.get('description')
    connection_string = data.get('connection_string')
    engine_id = data.get('engine_id')

    if not all([title, description, connection_string, engine_id]):
      return build_response(success=False, message="Todos los campos son obligatorios"), 400

    engine = session.query(Engine).get(engine_id)
    if not engine:
      return build_response(success=False, message="Motor no encontrado"), 404

    new_project = Project(
      title=title,
      description=description,
      connection_string=connection_string,
      engine_id=engine_id
    )
    session.add(new_project)
    session.commit()

    return build_response(
      data={"id": new_project.id},
      message="Proyecto creado exitosamente"
    ), 201

  except Exception as e:
    session.rollback()
    tb = traceback.format_exc()
    return handle_error(f"Error al crear proyecto: {str(e)}", tb)

def update_project(project_id, data):
  try:
    project = session.query(Project).get(project_id)
    if not project:
      return build_response(success=False, message="Proyecto no encontrado"), 404

    project.title = data.get('title', project.title)
    project.description = data.get('description', project.description)
    project.connection_string = data.get('connection_string', project.connection_string)
    project.engine_id = data.get('engine_id', project.engine_id)

    session.commit()
    return build_response(data={"id": project.id}, message="Proyecto actualizado exitosamente"), 200

  except Exception as e:
    session.rollback()
    tb = traceback.format_exc()
    return handle_error(f"Error al actualizar proyecto: {str(e)}", tb)

def delete_project(project_id):
  try:
    project = session.query(Project).get(project_id)
    if not project:
      return build_response(success=False, message="Proyecto no encontrado"), 404

    session.delete(project)
    session.commit()

    return build_response(data={"id": project.id}, message="Proyecto eliminado exitosamente"), 200

  except Exception as e:
    session.rollback()
    tb = traceback.format_exc()
    return handle_error(f"Error al eliminar proyecto: {str(e)}", tb)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++ 
# image
# ++++++++++++++++++++++++++++++++++++++++++++++++++++

def generate_plantuml_image(plantuml_code, output_dir="static/tmp"):
  Path(output_dir).mkdir(parents=True, exist_ok=True)

  timestamp = int(time.time())
  filename = f"diagram_{timestamp}.png"
  filepath = os.path.join(output_dir, filename)

  try:
    server = PlantUML(url='http://www.plantuml.com/plantuml/img/')
    
    # Este método existe en plantuml3 (verifica tu versión)
    image_data = server.processes(plantuml_code)
    
    with open(filepath, 'wb') as f:
      f.write(image_data)

    # Quitar "static/" del path para la URL
    relative_url = os.path.relpath(filepath, "static")

    return {
      "data": {
        "filepath": filepath,
        "filename": filename,
        "url": f"/{relative_url}"
      },
      "message": "Imagen generada correctamente",
      "success": True,
      "error": None
    }, 200

  except Exception as e:
    tb = traceback.format_exc()
    return {
      "data": None,
      "message": f"Error al generar UML: {str(e)}",
      "success": False,
      "error": tb
    }, 500
  
# ++++++++++++++++++++++++++++++++++++++++++++++++++++ 
# migrations
# ++++++++++++++++++++++++++++++++++++++++++++++++++++

def create_migrations(model, project):
  # Crear timestamp actual
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  
  # Obtener la ruta del directorio actual del proyecto
  project_root = os.getcwd()  # O usa os.path.dirname(os.path.abspath(__file__))
  
  # Crear ruta de la carpeta en la raíz del proyecto
  folder_path = os.path.join(project_root, "tmp", f"migrations_{timestamp}")

  try:
    # Crear la carpeta
    os.makedirs(folder_path, exist_ok=True)
    print(f"Carpeta creada: {folder_path}")
    
    # Ruta completa del archivo
    file_path = os.path.join(folder_path, "modelo.puml")
    
    # Escribir el contenido del modelo en el archivo
    with open(file_path, 'w', encoding='utf-8') as file:
      file.write(model)
    
    print(f"Archivo creado: {file_path}")

    db_type_dict = {
      'SQLite3': 'sqlite',
      'MySQL': 'mysql',
      'Postgres': 'postgres'
    }

    db_type = db_type_dict[project['engine']['name']]

    data, sucess = demo(folder_path, db_type)

    if sucess:
      return {
        "data": data,
        "message": "Migraciones generadas correctamente",
        "success": True,
        "error": None
      }, 200
    else:
      return handle_error(f"Error al crear las migraciones: {str(data)}")
    
  except Exception as e:
    print(f"Error al crear archivo: {str(e)}")
    tb = traceback.format_exc()
    return {
      "data": None,
      "message": f"Error al generar UML: {str(e)}",
      "success": False,
      "error": tb
    }, 500
  
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