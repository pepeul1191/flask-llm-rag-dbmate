-- migrate:up

CREATE TABLE permissions (
    id [INTEGER PRIMARY KEY AUTOINCREMENT],
    name VARCHAR(40),
    created DATETIME,
    updated DATETIME,
    role_id INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS permissions;