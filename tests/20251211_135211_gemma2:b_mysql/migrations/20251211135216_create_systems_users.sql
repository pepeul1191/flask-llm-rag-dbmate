-- migrate:up

CREATE TABLE systems_users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  system_id INT REFERENCES systems(id),
  user_id INT REFERENCES users(id),
  created DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS systems_users;