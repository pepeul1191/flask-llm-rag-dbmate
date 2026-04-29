-- migrate:up

CREATE TABLE programs ( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, image_url TEXT, pdf_url TEXT, max_participant_team INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, type_id INTEGER, FOREIGN KEY (type_id) REFERENCES program_types(id) );

-- migrate:down

DROP TABLE IF EXISTS PROGRAMS;