-- migrate:up

CREATE TABLE roles_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        created DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (role_id) REFERENCES roles(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

-- migrate:down

DROP TABLE IF EXISTS roles_users;