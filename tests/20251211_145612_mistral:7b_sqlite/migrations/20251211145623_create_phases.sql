-- migrate:up

CREATE TABLE phases ( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, init_date DATE, end_date DATE, delivery_deadline DATE, evaluation_deadline DATE, revaluation_deadline DATE, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, program_id INTEGER, FOREIGN KEY (program_id) REFERENCES programs(id) );

-- migrate:down

DROP TABLE IF EXISTS PHASES;