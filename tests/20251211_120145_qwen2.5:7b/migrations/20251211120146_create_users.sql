-- migrate:up

CREATE TABLE users (
  id INTEGER AUTO_INCREMENT,
  username VARCHAR(30) NOT NULL,
  password VARCHAR(40) NOT NULL,
  first_names VARCHAR(50),
  last_names VARCHAR(50),
  email VARCHAR(30),
  birth_date DATE,
  profile_picture VARCHAR(100),
  sex BOOLEAN,
  reset_key VARCHAR(30),
  country_id INTEGER,
  PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE IF EXISTS users;