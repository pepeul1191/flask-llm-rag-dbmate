#!/usr/bin/env python
# -*- coding: utf-8 -*-

# application/views.py

from io import BytesIO
from pathlib import Path

import markdown
from flask import Blueprint, render_template, send_file
from weasyprint import HTML


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


@view.route('/user-manual', methods=['GET'])
def user_manual():
    # application/views.py
    #        ↓
    # application/
    #        ↓
    # proyecto/
    #        ↓
    # README.md
    project_root = Path(__file__).resolve().parent.parent
    readme_path = project_root / 'README.md'

    # Leer README.md
    markdown_content = readme_path.read_text(encoding='utf-8')

    # Convertir Markdown a HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=[
            'extra',
            'tables',
            'fenced_code',
            'toc',
            'sane_lists',
        ]
    )

    # CSS para el PDF
    css = """
    @page {
        size: A4;
        margin: 2cm;
    }

    body {
        font-family: Arial, Helvetica, sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
    }

    h1 {
        font-size: 24pt;
        color: #222;
        border-bottom: 2px solid #ddd;
        padding-bottom: 8px;
        margin-top: 0;
    }

    h2 {
        font-size: 18pt;
        color: #333;
        margin-top: 30px;
    }

    h3 {
        font-size: 14pt;
        margin-top: 25px;
    }

    p {
        margin: 10px 0;
    }

    a {
        color: #1565c0;
    }

    code {
        font-family: monospace;
        background: #f4f4f4;
        padding: 2px 4px;
        border-radius: 3px;
    }

    pre {
        background: #f4f4f4;
        padding: 12px;
        border-radius: 5px;
        overflow-wrap: break-word;
        white-space: pre-wrap;
    }

    pre code {
        background: transparent;
        padding: 0;
    }

    blockquote {
        border-left: 4px solid #ccc;
        margin: 20px 0;
        padding: 5px 20px;
        color: #666;
        background: #fafafa;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }

    th,
    td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }

    th {
        background: #f5f5f5;
    }

    img {
        max-width: 100%;
        height: auto;
    }

    ul,
    ol {
        margin-bottom: 15px;
    }
    """

    # Generar PDF en memoria
    document = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            {css}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    pdf = HTML(
        string=document,
        base_url=str(project_root)
    ).write_pdf()

    # Devolver PDF
    return send_file(
        BytesIO(pdf),
        mimetype='application/pdf',
        as_attachment=False,
        download_name='user-manual.pdf'
    )
