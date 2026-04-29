-- migrate:up

CREATE TABLE systems_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,
    code INTEGER NOT NULL,
    FOREIGN KEY (worker_id) REFERENCES users(id)
);

-- migrate:down

DROP TABLE systems_users;