-- migrate:up

CREATE TABLE genres (
  id SERIAL PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE
);

-- migrate:down

DROP TABLE genres;