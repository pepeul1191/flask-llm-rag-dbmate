-- migrate:up

CREATE TABLE carrere_grades (
    id INT AUTO_INCREMENT PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS carrere_grades;