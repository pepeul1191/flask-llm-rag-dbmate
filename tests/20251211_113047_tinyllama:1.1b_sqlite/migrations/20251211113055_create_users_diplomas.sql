-- migrate:up

CREATE TABLE users_diplomas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title VARCHAR(50) NOT NULL,
        diploma_type VARCHAR(20) NOT NULL,
        diploma_date DATE NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

-- migrate:down

DROP TABLE IF EXISTS users_diplomas;