-- migrate:up

CREATE TABLE engines (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(20) NOT NULL,
  image VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE engines;