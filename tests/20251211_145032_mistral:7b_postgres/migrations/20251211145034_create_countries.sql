-- migrate:up

CREATE TABLE countries ( id SERIAL PRIMARY KEY, name VARCHAR(30) NOT NULL, male_demonym VARCHAR(40), female_demonym VARCHAR(40), flag_image VARCHAR(100) );

-- migrate:down

DROP TABLE IF EXISTS COUNTRIES;