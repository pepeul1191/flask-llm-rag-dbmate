-- migrate:up

CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username VARCHAR(30) NOT NULL,
  password VARCHAR(40) NOT NULL,
  first_names VARCHAR(50),
  last_names VARCHAR(50),
  email VARCHAR(30) NOT NULL,
  birth_date DATE,
  profile_picture VARCHAR(100),
  sex BOOLEAN
);

-- migrate:down

DROP TABLE IF EXISTS users;