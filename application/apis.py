#!/usr/bin/env python
# -*- coding: utf-8 -*-

# application/apis.py

from flask import Blueprint, jsonify
from application.services import fetch_engines

api = Blueprint(
  'application-apis', 
  __name__
)

@api.route('/api/v1/demo', methods=['GET'])
def index():
  return 'hola mundo'

@api.route('/api/v1/engines', methods=['GET'])
def list_engines():
  result = fetch_engines()
  status = 200
  if result['data'] == [] and result['success']:
    status = 400 
  elif result['success'] == False:
      status = 500 
  return jsonify(result), status