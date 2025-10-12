#!/usr/bin/env python
# -*- coding: utf-8 -*-

# application/apis.py

from flask import Blueprint, jsonify, request
from application.services import (
  fetch_engines as fetch_engines_service,
  create_project as create_project_service,
  update_project as update_project_service,
  delete_project as delete_project_service,
)

api = Blueprint(
  'application-apis', 
  __name__
)

@api.route('/api/v1/demo', methods=['GET'])
def index():
  return 'hola mundo'

@api.route('/api/v1/engines', methods=['GET'])
def list_engines():
  result = fetch_engines_service()
  status = 200
  if result['data'] == [] and result['success']:
    status = 400 
  elif result['success'] == False:
    status = 500 
  return jsonify(result), status

@api.route('/api/v1/projects', methods=['POST'])
def create_project():
  data = request.get_json()
  result, status = create_project_service(data)
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