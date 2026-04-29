-- migrate:up

CREATE TABLE mentors_spcialisms (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS mentors_spcialisms;