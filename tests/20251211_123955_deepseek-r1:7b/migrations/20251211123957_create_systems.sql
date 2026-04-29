-- migrate:up

CREATE TABLE systems (
    id [INTEGER PRIMARY KEY AUTOINCREMENT],
    name VARCHAR(40),
    description TEXT,
    repository VARCHAR(100),
    created DATETIME,
    updated DATETIME
);

-- migrate:down

DROP TABLE IF EXISTS systems;