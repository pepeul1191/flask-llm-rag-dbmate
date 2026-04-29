-- migrate:up

CREATE TABLE permissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(40) NOT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated DATETIME DEFAULT CURRENT_TIMESTAMP,
  role_id INTEGER,
  FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- migrate:down

DROP TABLE permissions;