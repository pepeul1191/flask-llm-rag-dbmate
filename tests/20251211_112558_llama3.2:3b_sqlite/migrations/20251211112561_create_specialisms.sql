-- migrate:up

CREATE TABLE specialisms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(70)
);

-- migrate:down

DROP TABLE IF EXISTS specialisms;