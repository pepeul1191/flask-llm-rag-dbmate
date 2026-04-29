-- migrate:up

CREATE TABLE periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    init_date DATE,
    end_date DATE
);

-- migrate:down

DROP TABLE IF EXISTS periods;