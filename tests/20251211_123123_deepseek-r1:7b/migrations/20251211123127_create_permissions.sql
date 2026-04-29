-- migrate:up

CREATE TABLE permissions (
    id AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40),
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME NOT NULL,
    role_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- migrate:down

DROP TABLE IF EXISTS permissions;