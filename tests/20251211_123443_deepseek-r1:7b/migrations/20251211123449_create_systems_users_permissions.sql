-- migrate:up

CREATE TABLE systems_users_permissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  system_id INTEGER,
  user_id INTEGER,
  permission_id INTEGER,
  created DATETIME,
  FOREIGN KEY (system_id) REFERENCES systems(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (permission_id) REFERENCES permissions(id)
);

-- migrate:down

DROP TABLE IF EXISTS systems_users_permissions;