-- migrate:up

CREATE TABLE devices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  brand VARCHAR(30),
  type VARCHAR(30),
  user_id INT,
  FOREIGN KEY (user_id) REFERENCES workers(id)
);

-- migrate:down

DROP TABLE IF EXISTS devices;