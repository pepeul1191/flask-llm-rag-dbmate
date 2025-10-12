# services/engine_service.py
import traceback
from application.models import Engine, Project
from sqlalchemy import text
from main.database import session

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

def fetch_projects():
  try:
    sql = text("""
      SELECT 
        P.id, 
        P.title, 
        P.description, 
        P.connection_string, 
        P.engine_id,
        E.name AS engine_name, 
        E.image AS engine_image,
        COUNT(V.id) AS versions_count,
        MAX(COALESCE(V.updated_at, V.created_at)) AS last_version_date

      FROM projects P
      JOIN engines E ON P.engine_id = E.id
      LEFT JOIN versions V ON P.id = V.project_id

      GROUP BY 
        P.id, P.title, P.description, P.connection_string, P.engine_id, E.name, E.image

      ORDER BY P.title ASC;
    """)

    result = session.execute(sql)
    print('1 ++++++++++++++++++++++')
    rows = result.fetchall()

    data = [
      {
        "id": row.id,
        "title": row.title,
        "description": row.description,
        "connection_string": row.connection_string,
        "engine_id": row.engine_id,
        "engine": {
          "id": row.engine_id,
          "name": row.engine_name,
          "image": row.engine_image
        },
        "versions_count": row.versions_count,
        "last_version_date": row.last_version_date if row.last_version_date else None
      }
      for row in rows
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