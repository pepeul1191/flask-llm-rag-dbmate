-- migrate:up

CREATE TABLE specialisms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(70) NOT NULL,
    FOREIGN KEY (name) REFERENCES 'specialisms'
);

-- migrate:down

DROP TABLE specialisms;