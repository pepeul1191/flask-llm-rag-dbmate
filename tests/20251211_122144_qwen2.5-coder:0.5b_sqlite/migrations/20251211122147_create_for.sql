-- migrate:up

Create table for roles
CREATE TABLE roles (
  id INTEGER PRIMARY KEY,
  name VARCHAR(40)
);

-- migrate:down

DROP TABLE IF EXISTS for;