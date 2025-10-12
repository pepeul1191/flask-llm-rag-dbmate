#!/usr/bin/env python
# -*- coding: utf-8 -*-

# application/views.py

from flask import Blueprint, render_template

view = Blueprint(
  'application-views', 
  __name__
)

@view.route('/', methods=['GET'])
@view.route('/projects', methods=['GET'])
@view.route('/about', methods=['GET'])
@view.route('/projects/<int:project_id>/edit', methods=['GET'])
def index(project_id=None):
  locals = {
    'title': 'Home',
    'nav_active': 'home',
    'message': '',
  }
  return render_template('index.html', locals=locals)

