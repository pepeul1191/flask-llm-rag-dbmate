-- migrate:up

CREATE TABLE periods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(10) NOT NULL,
    init_date DATE NOT NULL,
    end_date DATE NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS periods;