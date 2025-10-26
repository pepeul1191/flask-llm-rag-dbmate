#!/usr/bin/env python
# -*- coding: utf-8 -*-

# application/apis.py

from flask import Blueprint, jsonify, request
from application.services import (
  fetch_engines as fetch_engines_service,
  create_project as create_project_service,
  update_project as update_project_service,
  delete_project as delete_project_service,
  fetch_projects as fetch_projects_service,
  fetch_project as fetch_project_service,
  create_migrations as create_migrations_service,
  generate_plantuml_image,
)

api = Blueprint(
  'application-apis', 
  __name__
)

@api.route('/api/v1/demo', methods=['GET'])
def index():
  return 'hola mundo'

# ++++++++++++++++++++++++++++++++++++++++++++++++++++ 
# engines
# ++++++++++++++++++++++++++++++++++++++++++++++++++++

@api.route('/api/v1/engines', methods=['GET'])
def list_engines():
  result = fetch_engines_service()
  # Simplificar lógica de códigos de estado
  status_code = 200 if result['success'] else 500
  return jsonify(result), status_code

# ++++++++++++++++++++++++++++++++++++++++++++++++++++ 
# projects
# ++++++++++++++++++++++++++++++++++++++++++++++++++++

@api.route('/api/v1/projects', methods=['POST'])
def create_project():
  data = request.get_json()
  result, status = create_project_service(data)
  return jsonify(result), status

@api.route('/api/v1/projects', methods=['GET'])
def list_projects():
  result, status = fetch_projects_service()
  return jsonify(result), status

@api.route('/api/v1/projects/<int:project_id>', methods=['GET'])
def find_project(project_id):
  result, status = fetch_project_service(project_id)
  return jsonify(result), status

@api.route('/api/v1/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
  data = request.get_json()
  result, status = update_project_service(project_id, data)
  return jsonify(result), status

@api.route('/api/v1/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
  result, status = delete_project_service(project_id)
  return jsonify(result), status

# ++++++++++++++++++++++++++++++++++++++++++++++++++++ 
# image
# ++++++++++++++++++++++++++++++++++++++++++++++++++++

@api.route('/api/v1/image', methods=['POST'])
def create_image():
  data = request.get_json()
  result, status = generate_plantuml_image(data['content'])
  return jsonify(result), status

# ++++++++++++++++++++++++++++++++++++++++++++++++++++ 
# migrations
# ++++++++++++++++++++++++++++++++++++++++++++++++++++

@api.route('/api/v1/migrations/generate', methods=['POST'])
def create_migrations():
  data = request.get_json()
  result, status = create_migrations_service(data['model'], data['project'])
  return jsonify(result), status