-- migrate:up

CREATE TABLE periods ( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, init_date DATE, end_date DATE, program_id INTEGER, FOREIGN KEY (program_id) REFERENCES programs(id) );

-- migrate:down

DROP TABLE IF EXISTS PERIODS;