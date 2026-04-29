-- migrate:up

CREATE TABLE internals (
    id SERIAL PRIMARY KEY,
    code INT
);

-- migrate:down

DROP TABLE IF EXISTS internals;