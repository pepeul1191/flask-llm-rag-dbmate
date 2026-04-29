-- migrate:up

CREATE TABLE roles (
    id [INTEGER PRIMARY KEY AUTOINCREMENT],
    name VARCHAR(40),
    created DATETIME,
    updated DATETIME,
    system_id INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS roles;