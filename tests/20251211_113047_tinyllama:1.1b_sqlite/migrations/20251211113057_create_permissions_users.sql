-- migrate:up

CREATE TABLE permissions_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        permission_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        created DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (permission_id) REFERENCES permissions(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

-- migrate:down

DROP TABLE IF EXISTS permissions_users;