# MDE LLM SQL Generator

Este es un proyecto base que integra un backend en **Flask** con un frontend en **Svelte**. Usa `rollup` para compilar los assets y un entorno virtual de Python para aislar las dependencias del backend.

---

## 📦 Requisitos previos

- [Python 3.8+](https://www.python.org/)
- [Node.js 22.23.2 LTS](https://nodejs.org/)
- [Git](https://git-scm.com/)
- [Ollama 0.32.5](https://ollama.com/)

---

## 🐍 Crear entorno virtual (backend)

### Ollama

Instalar modelo

    $ ollama pull llama3.2:3b
    $ ollama pull nomic-embed-text

### Python

    $ sudo apt update
    $ sudo apt install pkg-config default-libmysqlclient-dev build-essential sqlite3 mysql-client postgresql-client libpq-dev
    $ python3 -m venv venv
    $ source venv\bin\activate
    $ pip install -r requirements.txt

### .env

    #### DBMATE
    DB=sqlite:db/app.db

### Migraciones con DBMATE

Instalar dependencias:
    
    $ npm install

Crear migración:

    $ npm run db:new <nombre-migración>

Ejecutar

    $ npm run db:up

Deshacer

    $ npm run db:rollback

Listar árbol

    $ tree -I 'node_modules|.git|__pycache__|venv|flask_session'

## .env

    #### DBMATE
    DB=sqlite:db/app.db

## 🐍 Ejecutar Programa

    $  
