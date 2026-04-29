-- migrate:up

Create table for users
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username VARCHAR(20),
  password VARCHAR(100)
);

-- migrate:down

DROP TABLE IF EXISTS for;