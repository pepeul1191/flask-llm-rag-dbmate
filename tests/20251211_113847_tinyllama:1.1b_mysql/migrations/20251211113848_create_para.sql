-- migrate:up

CREATE TABLE para cada tabla del diagrama UML.
3. Agregar las relaciones y atributos específicos del diagrama UML a cada tabla.
4. Utilizar los pasos 1-3 para generar un conjunto de migraciones SQL.

Después de analizar el diagrama, se identifican las entidades y sus correspondientes tablas en la base de datos MySQL:

**Entidad: document_types**

* Tabla: `document_types`
* Atributos:
 + `id` (PRIMARY KEY)
 + `name` (VARCHAR(22))
* Relaciones:
 + `foreign_key` a `program_types(id)`
* Atributos específicos:
 + `name` (VARCHAR(22))

**Entidad: industries**

* Tabla: `industries`
* Atributos:
 + `id` (PRIMARY KEY)
 + `name` (VARCHAR(30))
* Relaciones:
 + `foreign_key` a `program_types(id)`
* Atributos específicos:
 + `name` (VARCHAR(30))

**Entidad: specialisms**

* Tabla: `specialisms`
* Atributos:
 + `id` (PRIMARY KEY)
 + `name` (VARCHAR(70))
* Relaciones:
 + `foreign_key` a `document_types(id)`
+ `foreign_key` a `programs(id)`
* Atributos específicos:
 + `name` (VARCHAR(70))

**Entidad: carrere_grades**

* Tabla: `carrere_grades`
* Atributos:
 + `id` (PRIMARY KEY)
 + `name` (VARCHAR(40))
* Relaciones:
 + `foreign_key` a `document_types(id)`
+ `foreign_key` a `programs(id)`
* Atributos específicos:
 + `name` (VARCHAR(40))

**Entidad: carreres**

* Tabla: `carreres`
* Atributos:
 + `id` (PRIMARY KEY)
 + `name` (VARCHAR(40))
* Relaciones:
 + `foreign_key` a `carrere_grades(id)`
+ `foreign_key` a `program_types(id)`
+ `foreign_key` a `periods(id)`
* Atributos específicos:
 + `name` (VARCHAR(40))

**Entidad: program_types**

* Tabla: `program_types`
* Atributos:
 + `id` (PRIMARY KEY)
 + `name` (VARCHAR(30))
* Relaciones:
 + `foreign_key` a `carreres(id)`
+ `foreign_key` a `document_types(id)`
+ `foreign_key` a `nations(id)`
+ `foreign_key` a `periods(id)`
* Atributos específicos:
 + `name` (VARCHAR(30))

**Entidad: dni_types**

* Tabla: `dnis_types`
* Atributos:
 + `id` (PRIMARY KEY)
 + `name` (VARCHAR(30))
* Relaciones:
 + `foreign_key` a `carreres(id)`
+ `foreign_key` a `document_types(id)`
* Atributos específicos:
 + `name` (VARCHAR(30))

**Entidad: nations**

* Tabla: `nations`
* Atributos:
 + `id` (PRIMARY KEY)
 + `name` (VARCHAR(30))
* Relaciones:
 + `foreign_key` a `carreres(id)`
+ `foreign_key` a `document_types(id)`
+ `foreign_key` a `periods(id)`
* Atributos específicos:
 + `name` (VARCHAR(30))

**Entidad: periods**

* Tabla: `periods`
* Atributos:
 + `id` (PRIMARY KEY)
 + `name` (VARCHAR(10))
 + `init_date` (DATE) y `end_date` (DATE)
* Relaciones:
 + `foreign_key` a `carreres(id)`
+ `foreign_key` a `program_types(id)`
* Atributos específicos:
 + `name` (VARCHAR(10))

**Entidad: programs**

* Tabla: `programs`
* Atributos:
 + `id` (PRIMARY KEY)
 + `name` (VARCHAR(30))
 + `description` (TEXT) y `image_url` (VARCHAR(60)) y `pdf_url` (VARCHAR(60)) y `max_participant_team` (INT)
+ `foreign_key` a `carreres(id)`
+ `foreign_key` a `document_types(id)`
+ `foreign_key` a `nations(id)`
+ `foreign_key` a `periods(id)`
* Atributos específicos:
 + `name` (VARCHAR(30))

**Entidad: phases**

* Tabla: `phases`
* Atributos:
 + `id` (PRIMARY KEY)
 + `name` (VARCHAR(30))
 + `description` (TEXT) y `init_date` (DATE) y `end_date` (DATE) y `delivery_deadline` (DATE) y `evaluation_deadline` (DATE) y `revaluation_deadline` (DATE)
+ `foreign_key` a `carreres(id)`
+ `foreign_key` a `document_types(id)`
+ `foreign_key` a `nations(id)`
+ `foreign_key` a `periods(id)`
* Atributos específicos:
 + `name` (VARCHAR(30))

**Entidad: participants**

* Tabla: `participants`
* Atributos:
 + `id` (PRIMARY KEY)
 + `names` (VARCHAR(50))
 + `last_names` (VARCHAR(50))
 + `email` (VARCHAR(40)) y `phone` (VARCHAR(40)) y `dni` (VARCHAR(20))
+ `foreign_key` a `carreres(id)`
* Atributos específicos:
 + `names` (VARCHAR(50))

**Entidad: internals**

* Tabla: `internals`
* Atributos:
 + `id` (PRIMARY KEY)
 + `code` (INT)
* Relaciones:
 + `foreign_key` a `carreres(id)`
+ `foreign_key` a `program_types(id)`
* Atributos específicos:
 + `code` (INT)

**Entidad: externals**

* Tabla: `externals`
* Atributos:
 + `id` (PRIMARY KEY)
* Relaciones:
 + `foreign_key` a `carreres(id)`
+ `foreign_key` a `program_types(id)`
* Atributos específicos:
 + `id` (PRIMARY KEY)

**Entidad: workers**

* Tabla: `workers`
* Atributos:
 + `id` (PRIMARY KEY)
 + `names` (VARCHAR(50)) y `last_names` (VARCHAR(50))
 + `email` (VARCHAR(40))
 + `phone` (VARCHAR(40))
+ `foreign_key` a `carreres(id)`
+ `created_at` (DATETIME) y `updated_at` (DATETIME)
* Relaciones:
 + `foreign_key` a `program_types(id)`
+ `foreign_key` a `nations(id)`
+ `foreign_key` a `periods(id)`
* Atributos específicos:
 + `names` (VARCHAR(50))
+ `last_names` (VARCHAR(50))

**Entidad: external_workers**

* Tabla: `external_workers`
* Atributos:
 + `id` (PRIMARY KEY)
* Relaciones:
 + `foreign_key` a `carreres(id)`
+ `foreign_key` a `program_types(id)`
* Atributos específicos:
 + `id` (PRIMARY KEY)

**Entidad: internal_workers**

* Tabla: `internal_workers`
* Atributos:
 + `id` (PRIMARY KEY)
 + `code` (INT)
* Relaciones:
 + `foreign_key` a `carreres(id)`
+ `foreign_key` a `program_types(id)`
* Atributos específicos:
 + `code` (INT)

**Entidad: mentors**

* Tabla: `mentors`
* Atributos:
 + `id` (PRIMARY KEY)
* Relaciones:
 + `foreign_key` a `carreres(id)`
+ `foreign_key` a `document_types(id)`
+ `foreign_key` a `nations(id)`
+ `foreign_key` a `periods(id)`
* Atributos específicos:
 + `id` (PRIMARY KEY)

**Entidad: mentors_spcialisms**

* Tabla: `mentors_spcialisms`
* Atributos:
 + `id` (PRIMARY KEY)
* Relaciones:
 + `foreign_key` a `carreres(id)`
+ `foreign_key` a `document_types(id)`
+ `foreign_key` a `nations(id)`
+ `foreign_key` a `periods(id)`
* Atributos específicos:
 + `id` (PRIMARY KEY)

**ANALISIS FINAL**

Después de analizar el diagrama UML, se generan las migraciones SQL correspondientes:

```sql
CREATE TABLE document_types (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(22)
);

-- migrate:down

DROP TABLE IF EXISTS para;