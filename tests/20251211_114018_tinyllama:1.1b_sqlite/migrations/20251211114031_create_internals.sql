-- migrate:up

CREATE TABLE internals (
  id INTEGER PRIMARY KEY,
  code INT NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS internals;