-- migrate:up

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(30) UNIQUE NOT NULL,
    password VARCHAR(40) CHECK LENGTH(1 TO 20),
    first_names VARCHAR(50) NOT NULL,
    last_names VARCHAR(50) NOT NULL,
    email VARCHAR(30) UNIQUE NOT NULL,
    birth_date DATE NOT NULL,
    profile_picture VARCHAR(100),
    sex BOOLEAN DEFAULT false,
    reset_key VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS users;