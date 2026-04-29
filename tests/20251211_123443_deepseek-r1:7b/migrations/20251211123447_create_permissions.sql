-- migrate:up

CREATE TABLE permissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(40),
  created DATETIME,
  updated DATETIME,
  role_id INTEGER,
  FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- migrate:down

DROP TABLE IF EXISTS permissions;