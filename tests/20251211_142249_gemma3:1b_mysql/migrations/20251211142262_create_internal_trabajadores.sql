-- migrate:up

CREATE TABLE internal_trabajadores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code INT
);

-- migrate:down

DROP TABLE internal_trabajadores;