-- migrate:up

CREATE TABLE carrere_grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(40)
);

-- migrate:down

DROP TABLE IF EXISTS carrere_grades;