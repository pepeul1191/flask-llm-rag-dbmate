-- migrate:up

CREATE TABLE internals (
  id SERIAL PRIMARY KEY,
  code INT NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS internals;