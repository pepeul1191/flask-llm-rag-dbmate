-- migrate:up

CREATE TABLE carreres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(40)
);

-- migrate:down

DROP TABLE IF EXISTS carreres;