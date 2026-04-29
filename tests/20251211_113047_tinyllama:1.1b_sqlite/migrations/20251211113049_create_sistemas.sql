-- migrate:up

CREATE TABLE sistemas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(40) NOT NULL,
        description TEXT,
        repository VARCHAR(100) NOT NULL,
        created DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated DATETIME DEFAULT CURRENT_TIMESTAMP
    );

-- migrate:down

DROP TABLE IF EXISTS sistemas;