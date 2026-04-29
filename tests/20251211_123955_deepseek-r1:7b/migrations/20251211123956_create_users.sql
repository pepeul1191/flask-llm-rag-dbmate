-- migrate:up

CREATE TABLE users (
    id [INTEGER PRIMARY KEY AUTOINCREMENT],
    username VARCHAR(20),
    password VARCHAR(100),
    activation_key VARCHAR(30),
    reset_key VARCHAR(30),
    email VARCHAR(50),
    activated BOOLEAN,
    created DATETIME,
    updated DATETIME
);

-- migrate:down

DROP TABLE IF EXISTS users;