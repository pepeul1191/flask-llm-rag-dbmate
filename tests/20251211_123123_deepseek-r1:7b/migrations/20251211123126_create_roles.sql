-- migrate:up

CREATE TABLE roles (
    id AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40),
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME NOT NULL,
    system_id INTEGER NOT NULL FOREIGN KEY (systems.id)
);

-- migrate:down

DROP TABLE IF EXISTS roles;