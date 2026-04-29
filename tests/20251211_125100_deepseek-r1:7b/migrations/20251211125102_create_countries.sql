-- migrate:up

CREATE TABLE countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30),
    male_demonym VARCHAR(40),
    female_demonym VARCHAR(40),
    flag_image VARCHAR(100)
);

-- migrate:down

DROP TABLE IF EXISTS countries;