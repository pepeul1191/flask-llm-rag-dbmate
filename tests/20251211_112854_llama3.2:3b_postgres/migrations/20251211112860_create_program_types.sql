-- migrate:up

CREATE TABLE program_types (
  id SERIAL PRIMARY KEY,
  name VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS program_types;