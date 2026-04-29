-- migrate:up

CREATE TABLE phases (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(30) NOT NULL,
  description TEXT,
  init_date DATE,
  end_date DATE,
  delivery_deadline DATE,
  evaluation_deadline DATE,
  revaluation_deadline DATE,
  created_at DATETIME,
  updated_at DATETIME
);

-- migrate:down

DROP TABLE IF EXISTS phases;