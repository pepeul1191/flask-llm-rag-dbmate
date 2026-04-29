-- migrate:up

Create table for systems
CREATE TABLE systems (
  id INTEGER PRIMARY KEY,
  name VARCHAR(40)
);

-- migrate:down

DROP TABLE IF EXISTS for;