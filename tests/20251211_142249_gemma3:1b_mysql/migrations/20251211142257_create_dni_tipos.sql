-- migrate:up

CREATE TABLE dni_tipos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(20)
);

-- migrate:down

DROP TABLE dni_tipos;