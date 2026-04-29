-- migrate:up

CREATE TABLE dni_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS dni_types;