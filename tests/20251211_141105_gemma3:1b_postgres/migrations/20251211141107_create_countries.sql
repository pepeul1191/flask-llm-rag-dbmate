-- migrate:up

CREATE TABLE countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL,
    male_demonym VARCHAR(40) DEFAULT NULL,
    female_demonym VARCHAR(40) DEFAULT NULL,
    flag_image VARCHAR(100) DEFAULT NULL
);

-- migrate:down

DROP TABLE countries;