-- migrate:up

CREATE TABLE external_workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participants_id INTEGER NOT NULL,
    FOREIGN KEY (participants_id) REFERENCES users(id)
);

-- migrate:down

DROP TABLE external_workers;