-- migrate:up

CREATE TABLE roles ( id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(40), created DATETIME, updated DATETIME, system_id INTEGER, FOREIGN KEY (system_id) REFERENCES systems(id) );

-- migrate:down

DROP TABLE IF EXISTS ROLES;