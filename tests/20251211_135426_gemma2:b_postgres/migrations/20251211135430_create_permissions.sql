-- migrate:up

CREATE TABLE permissions (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL UNIQUE,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  role_id INTEGER REFERENCES roles(id)
);

-- migrate:down

DROP TABLE IF EXISTS permissions;