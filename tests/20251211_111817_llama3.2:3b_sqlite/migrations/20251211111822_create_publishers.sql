-- migrate:up

CREATE TABLE publishers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(50),
  logo VARCHAR(100)
);

-- migrate:down

DROP TABLE IF EXISTS publishers;