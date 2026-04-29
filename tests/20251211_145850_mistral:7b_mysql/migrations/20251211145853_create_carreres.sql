-- migrate:up

CREATE TABLE carreres ( id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(40) NOT NULL, carrere_grade_id INT, FOREIGN KEY (carrere_grade_id) REFERENCES carrere_grades(id) );

-- migrate:down

DROP TABLE IF EXISTS CARRERES;