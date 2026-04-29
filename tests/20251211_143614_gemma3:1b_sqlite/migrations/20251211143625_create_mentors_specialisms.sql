-- migrate:up

CREATE TABLE mentors_specialisms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(70) NOT NULL,
    FOREIGN KEY (name) REFERENCES 'specialisms'
);

-- migrate:down

DROP TABLE mentors_specialisms;