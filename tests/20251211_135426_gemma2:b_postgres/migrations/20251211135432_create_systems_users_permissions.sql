-- migrate:up

CREATE TABLE systems_users_permissions (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  system_id INTEGER REFERENCES systems_users(system_id) NOT NULL,
  user_id INTEGER REFERENCES users(id) NOT NULL,
  permission_id INTEGER REFERENCES permissions(id) NOT NULL,
  created DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS systems_users_permissions;