-- migrate:up

CREATE TABLE mentors (
  id INT AUTO_INCREMENT PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS mentors;