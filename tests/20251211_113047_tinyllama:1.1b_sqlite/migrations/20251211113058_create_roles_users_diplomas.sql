-- migrate:up

CREATE TABLE roles_users_diplomas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        diploma_type VARCHAR(20) NOT NULL,
        diploma_date DATE NOT NULL,
        FOREIGN KEY (role_id) REFERENCES roles(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

-- migrate:down

DROP TABLE IF EXISTS roles_users_diplomas;