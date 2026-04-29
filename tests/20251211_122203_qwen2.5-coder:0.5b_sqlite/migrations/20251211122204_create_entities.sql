-- migrate:up

Create table entities to create
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS entities;