-- migrate:up

CREATE TABLE industries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL,
    FOREIGN KEY (name) REFERENCES 'industries'
);

-- migrate:down

DROP TABLE industries;