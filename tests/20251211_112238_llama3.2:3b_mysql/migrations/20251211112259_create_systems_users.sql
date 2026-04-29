-- migrate:up

CREATE TABLE systems_users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  system_id INT,
  user_id INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (system_id) REFERENCES industries(id),
  FOREIGN KEY (user_id) REFERENCES workers(id)
);

-- migrate:down

DROP TABLE IF EXISTS systems_users;