# MDE LLM SQL Generator

Generador de migraciones DBMate usando PlantUML, LLM y RAG.

---

## Requisitos previos (Ubuntu 24.04)

- [Python 3.8+](https://www.python.org/)
- [Node.js 22.23.2 LTS](https://nodejs.org/)
- [Git](https://git-scm.com/)
- [Ollama 0.32.5](https://ollama.com/)

---

## Crear entorno virtual (backend)

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

## Ejecutar Programa (frontend + backend)

    $ npm run dev  

## Instrucciones

1: Hacer click en "Proyectos"

![Bienvenida](./docs/images/pic01.png)

2: Hacer click en "Crear Proyectos"

![Bienvenida](./docs/images/pic02.png)

3: Llenar el formulario con los datos del proyecto y hacer click en "Crear proyecto". Las cadenas de conexión tienen que ser en formato DBMate, como por ejemplo en caso de un servidor local:

Sqlite:
+ sqlite://home/pepe/Desktop/coa_concurso.sqlite
MyQL:
+ mysql://root:123@localhost:3306/northwind
PostgreSQL:
+ postgres://user:password@localhost:5432/quinua_smart

4: Luego dar click en "Ver Proyecto"

![Bienvenida](./docs/images/pic03.png)

5: Luego dar click en "Agregar Migraciones"

![Bienvenida](./docs/images/pic04.png)

6: Para subir el archivo de extensión .puml hay dos opciones, desde el botónt "Seleccionar Modelo" o arrastrando el archivo de PlantUML directamente. Luego dar click en "Agregar Migraciones"

![Bienvenida](./docs/images/pic05.png)

7: Automaticamente se verá el diagrama de base de datos renderizado. Luego dar click en "Generar Migraciones"

![Bienvenida](./docs/images/pic06.png)

8: Luego de generada las migraciones, es posible hacer una última verificación del contenido y orden de las mismas.
9: En caso de ser necesario puede editar el contenido de una migración haciendo click en "Actualizar Migración".
10: Finalmente hace click para "Ejecutar Migraciones" para desplegar las migraciones en la base de datos definida en el paso 3.

![Bienvenida](./docs/images/pic07.png)

Finalmente puede visualizar las tablas implementadas en su cliente de base de datos preferido.

![Bienvenida](./docs/images/pic08.png)

## Consideraciones del archivo .puml

Tiene considerar los siguiente:

+ Entidades y atributos en inglés.
+ Usar snake case para los nombres de tablas y atributos.
+ De preferencia el orden de aparación de las entidades se de la más fuerte a la más débil y normalizado.
+ Las llaves primarias se tienen que llamar "id" y son enteros.
+ Las llaves foráneas se debén de llamar con el nombre de la tabla al que hacen referencia en singular más "_id".

Ejemplo:

```txt
@startuml

entity users {
  * id : INTEGER
  --
  * username : VARCHAR(20)
  * password : VARCHAR(100)
  * activation_key : VARCHAR(30)
  * reset_key : VARCHAR(30)
  * email : VARCHAR(50)
  * activated : BOOLEAN
  * created : DATETIME
  * updated : DATETIME
}

entity systems {
  * id : INTEGER
  --
  * name : VARCHAR(40)
  * description : TEXT
  * repository : VARCHAR(100)
  * created : DATETIME
  * updated : DATETIME
}

entity roles {
  * id : INTEGER
  --
  * name : VARCHAR(40)
  * created : DATETIME
  * updated : DATETIME
  * system_id : INTEGER
}

entity permissions {
  * id : INTEGER
  --
  * name : VARCHAR(40)
  * created : DATETIME
  * updated : DATETIME
  * role_id : INTEGER
}

entity systems_users {
  * id : INTEGER
  --
  * system_id : INTEGER
  * user_id : INTEGER
  * created : DATETIME
}

entity systems_users_permissions {
  * id : INTEGER
  --
  * system_id : INTEGER
  * user_id : INTEGER
  * permission_id : INTEGER
  * created : DATETIME
}

' Relaciones
users -- systems_users : "has many"
systems_users -- systems : "belongs to"
systems_users -- users : "belongs to"
roles -- permissions : "has many"
permissions -- roles : "belongs to"
roles -- systems : "belongs to"
systems_users_permissions -- systems : "belongs to"
systems_users_permissions -- users : "belongs to"
systems_users_permissions -- permissions : "belongs to"

@enduml

```


# Usar el nuevo ollama

    $ sudo snap stop ollama
    $ sudo systemctl enable --now ollama
    $ ollama --version