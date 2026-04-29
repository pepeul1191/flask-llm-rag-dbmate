-- migrate:up

CREATE TABLE roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(40) NOT NULL,
        created DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        system_id INTEGER NOT NULL,
        FOREIGN KEY (system_id) REFERENCES sistemas(id)
    );

-- migrate:down

DROP TABLE IF EXISTS roles;