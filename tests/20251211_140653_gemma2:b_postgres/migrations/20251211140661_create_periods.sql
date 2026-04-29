-- migrate:up

CREATE TABLE periods (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(10) NOT NULL,
  init_date DATE,
  end_date DATE
);

-- migrate:down

DROP TABLE IF EXISTS periods;