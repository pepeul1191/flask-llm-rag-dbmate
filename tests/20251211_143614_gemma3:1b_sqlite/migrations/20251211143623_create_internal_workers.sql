-- migrate:up

CREATE TABLE internal_workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code INTEGER NOT NULL,
    FOREIGN KEY (code) REFERENCES systems_users(id)
);

-- migrate:down

DROP TABLE internal_workers;