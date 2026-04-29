-- migrate:up

CREATE TABLE countries (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(30),
  male_demonym VARCHAR(40),
  female_demonym VARCHAR(40),
  flag_image VARCHAR(100)
);

-- migrate:down

DROP TABLE countries;