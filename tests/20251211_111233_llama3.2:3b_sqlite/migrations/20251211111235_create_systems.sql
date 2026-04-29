-- migrate:up

CREATE TABLE systems (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(40) NOT NULL,
  description TEXT,
  repository VARCHAR(100),
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down

DROP TABLE systems;