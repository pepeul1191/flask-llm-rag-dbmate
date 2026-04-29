-- migrate:up

CREATE TABLE systems (
    id AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40),
    description TEXT,
    repository VARCHAR(100),
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS systems;