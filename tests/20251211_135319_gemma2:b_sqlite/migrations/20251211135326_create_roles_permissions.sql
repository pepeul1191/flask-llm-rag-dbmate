-- migrate:up

CREATE TABLE roles_permissions (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  role_id INTEGER REFERENCES roles(id) NOT NULL,
  permission_id INTEGER REFERENCES permissions(id) NOT NULL,
  created DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS roles_permissions;