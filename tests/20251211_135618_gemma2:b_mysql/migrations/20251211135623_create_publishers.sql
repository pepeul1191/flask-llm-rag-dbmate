-- migrate:up

CREATE TABLE publishers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) UNIQUE,
  logo VARCHAR(100) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS publishers;