-- migrate:up

CREATE TABLE IF NOT EXISTS Permissions(     id INTEGER PRIMARY KEY AUTOINCREMENT,  name TEXT UNIQUE not null ,        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,         updated_at   datetime on update current timestamp);

-- migrate:down

DROP TABLE IF EXISTS Permissions;