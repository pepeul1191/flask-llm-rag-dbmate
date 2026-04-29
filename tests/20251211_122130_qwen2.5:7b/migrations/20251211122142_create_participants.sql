-- migrate:up

CREATE TABLE participants (
    id SERIAL PRIMARY KEY,
    names VARCHAR(50) NOT NULL,
    last_names VARCHAR(50) NOT NULL,
    email VARCHAR(40),
    phone VARCHAR(40),
    dni VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dni_type_id INTEGER REFERENCES dni_types(id),
    nation_id INTEGER REFERENCES nations(id),
    user_id INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS participants;