-- migrate:up

CREATE TABLE roles (
  id INTEGER PRIMARY KEY,
  name VARCHAR(40)
);

-- migrate:down

DROP TABLE IF EXISTS roles;