-- migrate:up

CREATE TABLE IF NOT EXISTS UserPermissions(     id INTEGER PRIMARY KEY AUTOINCREMENT,      user_id integer not null references 'User.iD',   permission_ID Integer Not Null REFERENCES Permission (Id), created at DATETIME DEFAULT CURRENT
TIMESTAMP;

-- migrate:down

DROP TABLE IF EXISTS UserPermissions;