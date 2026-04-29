-- migrate:up

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    created DATETIME NOT NULL,
    updated DATETIME NOT NULL,
    system_id INTEGER,
    FOREIGN KEY (system_id) REFERENCES systems(id)
);

-- migrate:down

DROP TABLE IF EXISTS roles;