-- migrate:up

CREATE TABLE systems_users_permissions (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  system_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  permission_id INTEGER NOT NULL,
  created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (system_id) REFERENCES systems(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (permission_id) REFERENCES permissions(id)
);

-- migrate:down

DROP TABLE users;