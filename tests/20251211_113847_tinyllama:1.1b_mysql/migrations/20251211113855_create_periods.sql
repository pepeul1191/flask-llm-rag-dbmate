-- migrate:up

CREATE TABLE periods (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(10),
  init_date DATE,
  end_date DATE
);

-- migrate:down

DROP TABLE IF EXISTS periods;