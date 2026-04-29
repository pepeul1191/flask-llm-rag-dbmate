-- migrate:up

CREATE TABLE external_workers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  worker_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  FOREIGN KEY (worker_id) REFERENCES users (id)
);

-- migrate:down

DROP TABLE external_workers;