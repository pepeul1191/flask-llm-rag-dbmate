-- migrate:up

CREATE TABLE mentors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL,
    FOREIGN KEY (name) REFERENCES users(id)
);

-- migrate:down

DROP TABLE mentors;