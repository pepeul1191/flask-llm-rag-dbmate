-- migrate:up

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(20) NOT NULL,
    password VARCHAR(100) NOT NULL,
    activation_key VARCHAR(30),
    reset_key VARCHAR(30),
    email VARCHAR(50) NOT NULL,
    activated BOOLEAN NOT NULL,
    created DATETIME NOT NULL,
    updated DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS users;