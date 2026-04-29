-- migrate:up

CREATE TABLE industries (
  id INTEGER PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE
);

-- migrate:down

DROP TABLE IF EXISTS industries;