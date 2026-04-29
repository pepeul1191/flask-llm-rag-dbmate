-- migrate:up

CREATE TABLE carreres (
  id SERIAL PRIMARY KEY,
  name VARCHAR(40) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS carreres;