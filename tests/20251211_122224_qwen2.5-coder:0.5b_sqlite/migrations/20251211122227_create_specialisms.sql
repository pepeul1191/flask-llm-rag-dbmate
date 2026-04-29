-- migrate:up

Create table specialisms (id: INTEGER, name: VARCHAR(70))
CREATE TABLE specialisms (
  id INTEGER PRIMARY KEY,
  name VARCHAR(70)
);

-- migrate:down

DROP TABLE IF EXISTS specialisms;