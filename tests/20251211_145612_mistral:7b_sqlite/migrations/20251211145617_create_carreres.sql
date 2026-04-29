-- migrate:up

CREATE TABLE carreres ( id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(40) NOT NULL, grade_id INTEGER, FOREIGN KEY (grade_id) REFERENCES carrere_grades(id) );

-- migrate:down

DROP TABLE IF EXISTS CARRERES;