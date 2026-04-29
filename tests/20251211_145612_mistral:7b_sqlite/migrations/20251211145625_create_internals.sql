-- migrate:up

CREATE TABLE internals ( id INTEGER PRIMARY KEY AUTOINCREMENT, code INTEGER NOT NULL, participant_id INTEGER, FOREIGN KEY (participant_id) REFERENCES participants(id) );

-- migrate:down

DROP TABLE IF EXISTS INTERNALS;