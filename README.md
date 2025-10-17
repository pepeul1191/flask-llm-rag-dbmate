# MDE LLM SQL Generator

Este es un proyecto base que integra un backend en **Flask** con un frontend en **Svelte**. Usa `rollup` para compilar los assets y un entorno virtual de Python para aislar las dependencias del backend.

---

## 📦 Requisitos previos

- [Python 3.8+](https://www.python.org/)
- [Node.js y npm](https://nodejs.org/)
- [Git](https://git-scm.com/)

---

## 🐍 Crear entorno virtual (backend)

### En Windows:

    > python -m venv venv
    > venv\Scripts\activate.bat
    > pip install -r requirements.txt

### En Linux:

    $ python3 -m venv venv
    $ source venv\bin\activate
    $ pip install -r requirements.txt

### .env

    #### DBMATE
    DB=sqlite:db/app.db
    #### RAILS
    BASE_URL=http://localhost:3000/
    STATIC_URL=http://localhost:3000/
    USERNAME=admin
    PASSWORD=123

### Migraciones con DBMATE

Instalar dependencias:

    $ npm install

Crear migración:

    $ npm run db:new <nombre-migración>

Ejecutar

    $ npm run db:up

Deshacer

    $ npm run db:rollback

Ejemplos de código en Sqlite3

```sql
-- Crear una entidad fuerte
CREATE TABLE paises (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  nombre VARCHAR(40) NOT NULL,
  bandera_url VARCHAR(100) NOT NULL,
  gentilicio VARCHAR(30) NOT NULL
);
-- Crear una entidad debil
CREATE TABLE recurso_coleccion (
  id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  coleccion_id INTEGER NOT NULL,
  recurso_id INTEGER NOT NULL,
  FOREIGN KEY (coleccion_id) REFERENCES coleccion (id),
  FOREIGN KEY (recurso_id) REFERENCES recurso (id)
);
```
Listar árbol

    $ tree -I 'node_modules|.git|__pycache__|venv|flask_session'

### Ollama

Instalación de OLLAMA:

    $ sudo snap install ollama

## Comandos:

Iniciar el servicio de Ollama
    
    $ sudo systemctl start ollama

Habilitar para que inicie automáticamente
    
    $ sudo systemctl enable ollama

Verificar el estado del servicio
    
    $ sudo systemctl status ollama

Instalar modelo

    $ ollama pull llama3.2:3b