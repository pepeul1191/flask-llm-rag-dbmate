-- migrate:up

CREATE TABLE`.
2. USA el formato EXACTO de migración que se muestra a continuación.
3. PRESERVA los nombres ORIGINALES de las entidades y atributos.
4. Genera código SQL VÁLIDO para SQLite.

```sql
-- migrate:up

CREATE TABLE document_types (
  id INTEGER PRIMARY KEY,
  name VARCHAR(22) NOT NULL UNIQUE
);

-- migrate:down

DROP TABLE IF EXISTS document_types;