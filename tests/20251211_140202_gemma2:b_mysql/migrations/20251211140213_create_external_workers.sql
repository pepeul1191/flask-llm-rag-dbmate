-- migrate:up

CREATE TABLE external_workers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  worker_id INT REFERENCES workers(id)
);

-- migrate:down

DROP TABLE IF EXISTS external_workers;