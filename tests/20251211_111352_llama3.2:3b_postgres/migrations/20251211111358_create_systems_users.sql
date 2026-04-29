-- migrate:up

CREATE TABLE systems_users (
  id SERIAL PRIMARY KEY,
  system_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (system_id, user_id) REFERENCES users(user_id) REFERENCES systems_users(system_id)
);

-- migrate:down

DROP TABLE IF EXISTS systems_users;