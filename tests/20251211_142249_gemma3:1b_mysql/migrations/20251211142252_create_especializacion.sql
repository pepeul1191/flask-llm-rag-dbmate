-- migrate:up

CREATE TABLE especializacion (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(70)
);

-- migrate:down

DROP TABLE especializacion;