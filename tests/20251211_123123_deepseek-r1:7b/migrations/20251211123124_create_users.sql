-- migrate:up

CREATE TABLE users (
    id AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(20),
    password VARCHAR(100),
    activation_key VARCHAR(30) NOT NULL,
    reset_key VARCHAR(30) NOT NULL,
    email VARCHAR(50),
    activated BOOLEAN,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS users;