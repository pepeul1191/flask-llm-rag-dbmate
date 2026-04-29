-- migrate:up

CREATE TABLE dni_types (
  id INTEGER PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE
);

-- migrate:down

DROP TABLE IF EXISTS dni_types;