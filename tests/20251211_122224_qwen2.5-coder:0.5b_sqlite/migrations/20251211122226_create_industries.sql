-- migrate:up

Create table industries (id: INTEGER, name: VARCHAR(30))
CREATE TABLE industries (
  id INTEGER PRIMARY KEY,
  name VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS industries;