-- migrate:up

CREATE TABLE participants ( id INTEGER PRIMARY KEY AUTOINCREMENT, names TEXT NOT NULL, last_names TEXT NOT NULL, email TEXT NOT NULL, phone TEXT, dni TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, type_id INTEGER, nation_id INTEGER, user_id INTEGER, FOREIGN KEY (type_id) REFERENCES dni_types(id), FOREIGN KEY (nation_id) REFERENCES nations(id), FOREIGN KEY (user_id) REFERENCES users(id) );

-- migrate:down

DROP TABLE IF EXISTS PARTICIPANTS;