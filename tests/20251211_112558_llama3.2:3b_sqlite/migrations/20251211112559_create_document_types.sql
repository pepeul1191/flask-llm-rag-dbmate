-- migrate:up

CREATE TABLE document_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(22)
);

-- migrate:down

DROP TABLE IF EXISTS document_types;