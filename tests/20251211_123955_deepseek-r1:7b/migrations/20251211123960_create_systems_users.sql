-- migrate:up

CREATE TABLE systems_users (
    id [INTEGER PRIMARY KEY AUTOINCREMENT],
    system_id INTEGER,
    user_id INTEGER,
    created DATETIME,
    updated DATETIME
);

-- migrate:down

DROP TABLE IF EXISTS systems_users;