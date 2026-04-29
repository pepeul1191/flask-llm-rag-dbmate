-- migrate:up

CREATE TABLE publishers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50),
  logo VARCHAR(100)
);

-- migrate:down

DROP TABLE publishers;