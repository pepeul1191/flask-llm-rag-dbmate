-- migrate:up

CREATE TABLE nations (
  id INTEGER PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE
);

-- migrate:down

DROP TABLE IF EXISTS nations;