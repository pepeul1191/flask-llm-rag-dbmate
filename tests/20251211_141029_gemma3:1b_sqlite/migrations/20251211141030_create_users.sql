-- migrate:up

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username VARCHAR(255) NOT NULL,
  password VARCHAR(40) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  birth_date DATE,
  profile_picture VARCHAR(100),
  sex BOOLEAN,
  reset_key VARCHAR(30),
  country_id INTEGER,
  created DATETIME,
  updated DATETIME
);

-- migrate:down

DROP TABLE users;