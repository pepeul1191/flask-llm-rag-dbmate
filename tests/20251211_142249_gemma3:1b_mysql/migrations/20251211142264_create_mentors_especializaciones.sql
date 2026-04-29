-- migrate:up

CREATE TABLE mentors_especializaciones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(70)
);

-- migrate:down

DROP TABLE mentors_especializaciones;