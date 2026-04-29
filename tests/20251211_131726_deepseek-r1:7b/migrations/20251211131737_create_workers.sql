-- migrate:up

CREATE TABLE workers (
    id SERIAL PRIMARY KEY,
    names VARCHAR(50),
    last_names VARCHAR(50),
    email VARCHAR(40),
    phone VARCHAR(40),
    created_at DATETIME,
    updated_at DATETIME
);

-- migrate:down

DROP TABLE IF EXISTS workers;