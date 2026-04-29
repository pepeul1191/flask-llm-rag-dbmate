-- migrate:up

CREATE TABLE roles (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL UNIQUE,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  system_id INTEGER REFERENCES systems(id)
);

-- migrate:down

DROP TABLE IF EXISTS roles;