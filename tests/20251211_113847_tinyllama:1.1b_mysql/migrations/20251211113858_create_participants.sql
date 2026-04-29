-- migrate:up

CREATE TABLE participants (
  id INT AUTO_INCREMENT PRIMARY KEY,
  names VARCHAR(50),
  last_names VARCHAR(50),
  email VARCHAR(40),
  phone VARCHAR(40),
  dni VARCHAR(20)
);

-- migrate:down

DROP TABLE IF EXISTS participants;