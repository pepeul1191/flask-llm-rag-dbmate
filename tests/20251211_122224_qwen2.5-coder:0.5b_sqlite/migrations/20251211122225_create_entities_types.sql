-- migrate:up

Create table entities_types (id: INTEGER, name: VARCHAR(22))
CREATE TABLE document_types (
  id INTEGER PRIMARY KEY,
  name VARCHAR(22)
);

-- migrate:down

DROP TABLE IF EXISTS entities_types;