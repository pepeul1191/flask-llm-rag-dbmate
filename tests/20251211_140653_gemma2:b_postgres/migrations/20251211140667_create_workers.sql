-- migrate:up

CREATE TABLE workers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  names VARCHAR(50) NOT NULL,
  last_names VARCHAR(50) NOT NULL,
  email VARCHAR(40) NOT NULL,
  phone VARCHAR(40) NOT NULL,
  created_at DATETIME,
  updated_at DATETIME
);

-- migrate:down

DROP TABLE IF EXISTS workers;