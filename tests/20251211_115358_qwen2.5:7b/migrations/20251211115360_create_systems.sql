-- migrate:up

CREATE TABLE systems (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    description TEXT,
    repository VARCHAR(100),
    created DATETIME NOT NULL,
    updated DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS systems;