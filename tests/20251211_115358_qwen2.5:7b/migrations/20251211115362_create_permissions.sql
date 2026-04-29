-- migrate:up

CREATE TABLE permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    created DATETIME NOT NULL,
    updated DATETIME NOT NULL,
    role_id INTEGER,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- migrate:down

DROP TABLE IF EXISTS permissions;