-- migrate:up

CREATE TABLE phases (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(10) NOT NULL,
  init_date DATE NOT NULL,
  end_date DATE NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS phases;