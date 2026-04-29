-- migrate:up

CREATE TABLE program_types (
  id INTEGER PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE
);

-- migrate:down

DROP TABLE IF EXISTS program_types;