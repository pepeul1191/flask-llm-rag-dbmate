-- migrate:up

CREATE TABLE participants (
  id INT PRIMARY KEY AUTO_INCREMENT,
  names VARCHAR(50) NOT NULL,
  last_names VARCHAR(50) NOT NULL,
  email VARCHAR(40) NOT NULL,
  phone VARCHAR(40) NOT NULL,
  dni VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS participants;