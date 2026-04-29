-- migrate:up

CREATE TABLE mentors (
    id SERIAL PRIMARY KEY,
    worker_id INTEGER REFERENCES workers(id) ON DELETE CASCADE
);

-- migrate:down

DROP TABLE IF EXISTS mentors;