-- migrate:up

CREATE TABLE specialisms (
  id INTEGER PRIMARY KEY,
  name VARCHAR(70) NOT NULL UNIQUE
);

-- migrate:down

DROP TABLE IF EXISTS specialisms;