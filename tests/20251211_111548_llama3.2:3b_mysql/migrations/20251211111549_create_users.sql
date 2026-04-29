-- migrate:up

CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(30),
  password VARCHAR(40),
  first_names VARCHAR(50),
  last_names VARCHAR(50),
  email VARCHAR(30),
  birth_date DATE,
  profile_picture VARCHAR(100),
  sex BOOLEAN,
  reset_key VARCHAR(30),
  country_id INT,
  FOREIGN KEY (country_id) REFERENCES countries(id)
);

-- migrate:down

DROP TABLE users;