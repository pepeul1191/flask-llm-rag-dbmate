-- migrate:up

CREATE TABLE external_workers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  worker_id INT NOT NULL,
  FOREIGN key (worker_id) references workers(id)
);

-- migrate:down

DROP TABLE IF EXISTS external_workers;