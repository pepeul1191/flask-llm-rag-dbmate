-- migrate:up

CREATE TABLE workers (
    id SERIAL PRIMARY KEY,
    names VARCHAR(50) NOT NULL,
    last_names VARCHAR(50) NOT NULL,
    email VARCHAR(40),
    phone VARCHAR(40),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS workers;