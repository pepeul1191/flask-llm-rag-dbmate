-- migrate:up

CREATE TABLE systems_users (
  id SERIAL PRIMARY KEY,
  system_id INTEGER NOT NULL REFERENCES systems(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  created DATE NOT NULL DEFAULT CURRENT_DATE
);

-- migrate:down

DROP TABLE IF EXISTS systems_users;