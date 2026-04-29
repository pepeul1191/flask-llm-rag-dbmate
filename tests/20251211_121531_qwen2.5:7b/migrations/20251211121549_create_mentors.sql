-- migrate:up

CREATE TABLE mentors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER,
    FOREIGN KEY (worker_id) REFERENCES workers(id)
);

-- migrate:down

DROP TABLE IF EXISTS mentors;