-- migrate:up

CREATE TABLE IF NOT EXISTS UsersRoles(      id INTEGER PRIMARY KEY AUTOINCREMENT,        user_id integer not null references  User.iD ,     role_ID Integer Not Null REFERENCES Role (Id), created at DATETIME DEFAULT CURRENT
TIMESTAMP;

-- migrate:down

DROP TABLE IF EXISTS UsersRoles;