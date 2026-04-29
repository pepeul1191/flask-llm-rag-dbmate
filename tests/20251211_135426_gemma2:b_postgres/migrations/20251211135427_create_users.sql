-- migrate:up

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(20) NOT NULL UNIQUE,
  password VARCHAR(100) NOT NULL,
  activation_key VARCHAR(30) UNIQUE,
  reset_key VARCHAR(30) UNIQUE,
  email VARCHAR(50) UNIQUE,
  activated BOOLEAN NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS users;