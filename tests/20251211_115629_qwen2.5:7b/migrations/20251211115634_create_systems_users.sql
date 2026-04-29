-- migrate:up

CREATE TABLE systems_users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  system_id INTEGER,
  user_id INTEGER,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (system_id) REFERENCES systems(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- migrate:down

DROP TABLE IF EXISTS systems_users;