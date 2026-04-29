-- migrate:up

CREATE TABLE roles (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  system_id INT REFERENCES systems(id)
);

-- migrate:down

DROP TABLE IF EXISTS roles;