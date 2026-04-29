-- migrate:up

CREATE TABLE periodos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(10)
);

-- migrate:down

DROP TABLE periodos;