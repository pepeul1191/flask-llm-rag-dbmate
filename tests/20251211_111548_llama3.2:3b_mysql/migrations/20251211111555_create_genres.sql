-- migrate:up

CREATE TABLE genres (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(30)
);

-- migrate:down

DROP TABLE genres;