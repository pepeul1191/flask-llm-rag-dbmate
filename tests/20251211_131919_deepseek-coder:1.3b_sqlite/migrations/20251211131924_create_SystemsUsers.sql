-- migrate:up

CREATE Table If Not Exists SystemsUsers(     id INTEGER PRIMARY KEY AUTOINCREMENT ,    system_id integer not null references  System.sId,      user_ID Integer NOT NULL REFERENCES Users (iD), created at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- migrate:down

DROP TABLE IF EXISTS SystemsUsers;