-- migrate:up

CREATE TABLE phases (
    id SERIAL PRIMARY KEY,
    program_id INTEGER REFERENCES programs(id) ON DELETE CASCADE,
    name VARCHAR(30) NOT NULL,
    description TEXT,
    init_date DATE NOT NULL,
    end_date DATE NOT NULL,
    delivery_deadline DATE,
    evaluation_deadline DATE,
    revaluation_deadline DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down

DROP TABLE IF EXISTS phases;