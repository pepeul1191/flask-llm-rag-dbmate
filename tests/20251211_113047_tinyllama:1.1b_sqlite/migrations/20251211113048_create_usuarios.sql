-- migrate:up

CREATE TABLE usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(20) NOT NULL,
        password VARCHAR(100) NOT NULL,
        activation_key VARCHAR(30) NOT NULL,
        reset_key VARCHAR(30) NOT NULL,
        email VARCHAR(50) NOT NULL,
        created DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated DATETIME DEFAULT CURRENT_TIMESTAMP
    );

-- migrate:down

DROP TABLE IF EXISTS usuarios;