-- migrate:up

CREATE Table If Not Exists Roles(      id INTEGER PRIMARY KEY AUTOINCREMENT,       name TEXT UNIQUE NOT NULL ,        system_id integer not null references systems (id),     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,         updated_at 
DATETIME ON UPDATECURRENT_TIMESTAMP);

-- migrate:down

DROP TABLE IF EXISTS Roles;