-- migrate:up

CREATE TABLE systems_users_permissions (
  id SERIAL PRIMARY KEY,
  system_id INTEGER NOT NULL REFERENCES systems(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  permission_id INTEGER NOT NULL REFERENCES permissions(id),
  created DATE NOT NULL DEFAULT CURRENT_DATE
);

-- migrate:down

DROP TABLE IF EXISTS systems_users_permissions;