-- migrate:up

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username VARCHAR(20) NOT NULL UNIQUE,
  password VARCHAR(100) NOT NULL,
  activation_key VARCHAR(30) NOT NULL,
  reset_key VARCHAR(30) NOT NULL,
  email VARCHAR(50) NOT NULL,
  activated BOOLEAN,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  FOREIGN KEY (username) REFERENCES users(id)
);

-- migrate:down

DROP TABLE users;