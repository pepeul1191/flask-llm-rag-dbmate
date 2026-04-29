-- migrate:up

CREATE TABLE internal_workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code INT
);

-- migrate:down

DROP TABLE IF EXISTS internal_workers;