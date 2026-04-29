-- migrate:up

CREATE TABLE mentors_spcialisms (
    id INT AUTO_INCREMENT PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS mentors_spcialisms;