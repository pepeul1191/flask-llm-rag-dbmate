-- migrate:up

CREATE TABLE documento_tipos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(22)
);

-- migrate:down

DROP TABLE documento_tipos;