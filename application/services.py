# services/engine_service.py
import traceback
from application.models import Engine, Project
from main.database import session

def build_response(data=None, message="Operación exitosa"):
  return {
    "data": data,
    "message": message,
    "success": True,
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

def fetch_engines():
  try:
    engines = session.query(Engine).order_by(Engine.name.asc()).all()
    message="Lista de motores de bases de datos obtenida exitosamente"
    data = [
      {
        "id": engine.id,
        "name": engine.name,
        "image": engine.image
      }
      for engine in engines
    ]
    if data == []:
      return build_response(data=[], message=message)
    else:
      return build_response(data=data, message=message)
  except Exception as e:
    tb = traceback.format_exc()
    return handle_error(f"Error al obtener motores: {str(e)}", tb)

def list_projects():
  try:
    projects = session.query(Project).order_by(Project.title.asc()).all()
    data = [
      {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "connection_string": p.connection_string,
        "engine_id": p.engine_id,
        "engine": {
          "id": p.engine.id,
          "name": p.engine.name,
          "image": p.engine.image
        } if p.engine else None
      }
      for p in projects
    ]
    return build_response(data=data, message="Lista de proyectos obtenida exitosamente"), 200
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