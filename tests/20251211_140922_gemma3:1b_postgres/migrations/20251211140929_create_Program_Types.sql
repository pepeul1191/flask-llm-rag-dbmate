-- migrate:up

CREATE TABLE  Program_Types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(30) NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  repository VARCHAR(100) NOT NULL
);

-- migrate:down

DROP TABLE Program_Types;