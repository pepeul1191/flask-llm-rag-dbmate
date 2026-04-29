-- migrate:up

CREATE TABLE permissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(40) NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  role_id INTEGER NOT NULL,
  FOREIGN KEY (role_id) REFERENCES roles (id)
);

-- migrate:down

DROP TABLE permissions;