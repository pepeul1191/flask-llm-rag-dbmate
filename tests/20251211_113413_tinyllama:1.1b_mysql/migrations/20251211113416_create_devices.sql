-- migrate:up

CREATE TABLE devices (
  id INT PRIMARY KEY AUTO_INCREMENT,
  brand VARCHAR(30) NOT NULL,
  type VARCHAR(30) NOT NULL,
  user_id INT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- migrate:down

DROP TABLE IF EXISTS devices;