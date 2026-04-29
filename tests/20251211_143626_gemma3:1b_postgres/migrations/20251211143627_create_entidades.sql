-- migrate:up

CREATE TABLE entidades (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre VARCHAR(255) NOT NULL,
  tipo_primary_key VARCHAR(255) NOT NULL,
  PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE entidades;