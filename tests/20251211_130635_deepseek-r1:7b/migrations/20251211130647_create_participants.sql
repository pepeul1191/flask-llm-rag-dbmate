-- migrate:up

CREATE TABLE participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    names VARCHAR(50),
    last_names VARCHAR(50),
    email VARCHAR(40),
    phone VARCHAR(40),
    dni VARCHAR(20),
    created_at DATETIME,
    updated_at DATETIME
);

-- migrate:down

DROP TABLE IF EXISTS participants;