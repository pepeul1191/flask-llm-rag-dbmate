-- migrate:up

CREATE TABLE specialisms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(70) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS specialisms;