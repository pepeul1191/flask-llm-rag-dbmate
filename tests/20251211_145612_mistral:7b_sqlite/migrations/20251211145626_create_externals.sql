-- migrate:up

CREATE TABLE externals ( id INTEGER PRIMARY KEY AUTOINCREMENT, participant_id INTEGER, FOREIGN KEY (participant_id) REFERENCES participants(id) );

-- migrate:down

DROP TABLE IF EXISTS EXTERNALS;