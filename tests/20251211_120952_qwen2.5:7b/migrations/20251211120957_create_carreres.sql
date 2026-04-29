-- migrate:up

CREATE TABLE carreres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    grade_id INT,
    FOREIGN KEY (grade_id) REFERENCES carrere_grades(id)
);

-- migrate:down

DROP TABLE IF EXISTS carreres;