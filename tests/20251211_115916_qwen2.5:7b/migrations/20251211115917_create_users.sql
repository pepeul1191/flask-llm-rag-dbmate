-- migrate:up

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(20) NOT NULL,
    password VARCHAR(100) NOT NULL,
    activation_key VARCHAR(30),
    reset_key VARCHAR(30),
    email VARCHAR(50),
    activated BOOLEAN,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP
);

-- migrate:down

DROP TABLE IF EXISTS users;