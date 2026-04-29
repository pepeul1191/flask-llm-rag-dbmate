-- migrate:up

CREATE TABLE sistemas_users_diplomas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        diploma_type VARCHAR(20) NOT NULL,
        diploma_date DATE NOT NULL,
        FOREIGN KEY (system_id) REFERENCES sistemas(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

-- migrate:down

DROP TABLE IF EXISTS sistemas_users_diplomas;