-- migrate:up

CREATE TABLE systems_users_permissions (
  id SERIAL PRIMARY KEY,
  system_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  permission_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (system_id, user_id, permission_id) REFERENCES permissions(id)
);

-- migrate:down

DROP TABLE users;