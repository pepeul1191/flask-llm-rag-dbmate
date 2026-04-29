-- migrate:up

CREATE TABLE sistemas_users_diplomas_permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        permission_id INTEGER NOT NULL,
        diploma_type VARCHAR(20) NOT NULL,
        diploma_date DATE NOT NULL,
        created DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (system_id) REFERENCES sistemas(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (permission_id) REFERENCES permissions(id)
    );

-- migrate:down

DROP TABLE IF EXISTS sistemas_users_diplomas_permissions;