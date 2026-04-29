-- migrate:up

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username VARCHAR(20) NOT NULL,
  password VARCHAR(100) NOT NULL,
  activation_key VARCHAR(30),
  reset_key VARCHAR(30),
  email VARCHAR(50) NOT NULL,
  activated BOOLEAN DEFAULT 0,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down

DROP TABLE users;