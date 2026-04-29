-- migrate:up

CREATE TABLE mentors_spcialisms (
  id INT PRIMARY KEY AUTO_INCREMENT,
  worker_id INT REFERENCES workers(id)
);

-- migrate:down

DROP TABLE IF EXISTS mentors_spcialisms;