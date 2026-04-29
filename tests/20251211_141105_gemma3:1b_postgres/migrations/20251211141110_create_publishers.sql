-- migrate:up

CREATE TABLE publishers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,
    logo VARCHAR(100) DEFAULT NULL
);

-- migrate:down

DROP TABLE publishers;