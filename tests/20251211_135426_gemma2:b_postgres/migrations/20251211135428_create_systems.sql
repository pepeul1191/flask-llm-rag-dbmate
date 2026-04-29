-- migrate:up

CREATE TABLE systems (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL UNIQUE,
  description TEXT,
  repository VARCHAR(100) NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS systems;