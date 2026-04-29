-- migrate:up

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(30) UNIQUE,
  password VARCHAR(40),
  first_names VARCHAR(50),
  last_names VARCHAR(50),
  email VARCHAR(30),
  birth_date DATE,
  profile_picture VARCHAR(100),
  sex BOOLEAN,
  reset_key VARCHAR(30),
  country_id INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS users;