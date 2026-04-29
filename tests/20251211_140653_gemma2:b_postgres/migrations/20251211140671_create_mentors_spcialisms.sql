-- migrate:up

CREATE TABLE mentors_spcialisms (
  id INT PRIMARY KEY AUTO_INCREMENT,
  mentor_id INT NOT NULL,
  specialism_id INT NOT NULL,
  FOREIGN KEY (mentor_id) REFERENCES mentors(id)
  FOREIGN KEY (specialism_id) REFERENCES specialisms(id)
);

-- migrate:down

DROP TABLE IF EXISTS mentors_spcialisms;