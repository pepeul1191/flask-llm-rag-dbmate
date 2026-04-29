-- migrate:up

CREATE TABLE dni_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS dni_types;