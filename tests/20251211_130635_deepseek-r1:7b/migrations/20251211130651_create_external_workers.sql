-- migrate:up

CREATE TABLE external_workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT
);

-- migrate:down

DROP TABLE IF EXISTS external_workers;