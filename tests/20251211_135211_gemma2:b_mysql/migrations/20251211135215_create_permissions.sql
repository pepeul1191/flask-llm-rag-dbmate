-- migrate:up

CREATE TABLE permissions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  role_id INT REFERENCES roles(id)
);

-- migrate:down

DROP TABLE IF EXISTS permissions;