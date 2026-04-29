-- migrate:up

CREATE TABLE countries (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(30) NOT NULL,
  male_demonym VARCHAR(40) NOT NULL,
  female_demonym VARCHAR(40) NOT NULL,
  flag_image VARCHAR(100) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS countries;