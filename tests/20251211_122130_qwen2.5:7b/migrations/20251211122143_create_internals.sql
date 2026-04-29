-- migrate:up

CREATE TABLE internals (
    id SERIAL PRIMARY KEY,
    code INT NOT NULL,
    participant_id INTEGER REFERENCES participants(id) ON DELETE CASCADE,
    period_id INTEGER REFERENCES periods(id)
);

-- migrate:down

DROP TABLE IF EXISTS internals;