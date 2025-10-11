# services/engine_service.py
import traceback
from application.models import Engine
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
