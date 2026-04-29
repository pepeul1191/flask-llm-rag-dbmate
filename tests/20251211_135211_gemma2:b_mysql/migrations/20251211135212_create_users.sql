-- migrate:up

CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(20) NOT NULL,
  password VARCHAR(100) NOT NULL,
  activation_key VARCHAR(30) NOT NULL,
  reset_key VARCHAR(30) NOT NULL,
  email VARCHAR(50) NOT NULL,
  activated BOOLEAN NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS users;