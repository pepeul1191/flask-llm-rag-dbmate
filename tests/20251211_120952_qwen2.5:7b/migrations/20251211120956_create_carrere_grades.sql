-- migrate:up

CREATE TABLE carrere_grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS carrere_grades;