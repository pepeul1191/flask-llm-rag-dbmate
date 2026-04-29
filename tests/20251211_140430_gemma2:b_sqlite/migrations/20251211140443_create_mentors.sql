-- migrate:up

CREATE TABLE mentors (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS mentors;