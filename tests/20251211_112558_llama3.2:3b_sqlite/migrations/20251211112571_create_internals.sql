-- migrate:up

CREATE TABLE internals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS internals;