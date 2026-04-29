-- migrate:up

CREATE TABLE workers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  names VARCHAR(50) NOT NULL,
  last_names VARCHAR(50) NOT NULL,
  email VARCHAR(40) NOT NULL,
  phone VARCHAR(40) NOT NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  foreign key (worker_id) references workers(id)
);

-- migrate:down

DROP TABLE IF EXISTS workers;