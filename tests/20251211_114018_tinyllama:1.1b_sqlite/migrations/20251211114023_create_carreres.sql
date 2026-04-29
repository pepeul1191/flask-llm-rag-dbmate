-- migrate:up

CREATE TABLE carreres (
  id INTEGER PRIMARY KEY,
  name VARCHAR(40) NOT NULL UNIQUE
);

-- migrate:down

DROP TABLE IF EXISTS carreres;