-- migrate:up

CREATE TABLE nations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(30)
);

-- migrate:down

DROP TABLE nations;