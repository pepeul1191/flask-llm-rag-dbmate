-- migrate:up

CREATE TABLE carreres ( id SERIAL PRIMARY KEY, name VARCHAR(40) NOT NULL, carrere_grade_id INTEGER REFERENCES carrere_grades(id) );

-- migrate:down

DROP TABLE IF EXISTS CARRERES;