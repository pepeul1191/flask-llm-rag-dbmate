-- migrate:up

CREATE TABLE IF NOT EXISTS PermissionsSystems(     id INTEGER PRIMARY KEY AUTOINCREMENT,    permission_id integer not null references permissons.Id ,   system_ID Integer Not Null REFERENCES Systems (iD), created at DATETIME DEFAULT CURRENT
TIMESTAMP;

-- migrate:down

DROP TABLE IF EXISTS PermissionsSystems;