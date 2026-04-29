-- migrate:up

CREATE TABLE devices (
  id INT PRIMARY KEY AUTO_INCREMENT,
  brand VARCHAR(30),
  type VARCHAR(30),
  user_id INT,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- migrate:down

DROP TABLE devices;