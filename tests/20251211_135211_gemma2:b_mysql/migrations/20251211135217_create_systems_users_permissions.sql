-- migrate:up

CREATE TABLE systems_users_permissions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  system_id INT REFERENCES systems(id),
  user_id INT REFERENCES users(id),
  permission_id INT REFERENCES permissions(id),
  created DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS systems_users_permissions;