-- migrate:up

CREATE TABLE programs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(30),
  description TEXT,
  image_url VARCHAR(60),
  pdf_url VARCHAR(60),
  max_participant_team INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- migrate:down

DROP TABLE IF EXISTS programs;