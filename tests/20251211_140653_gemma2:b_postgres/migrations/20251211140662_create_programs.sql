-- migrate:up

CREATE TABLE programs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(30) NOT NULL,
  description TEXT,
  image_url VARCHAR(60) NOT NULL,
  pdf_url VARCHAR(60) NOT NULL,
  max_participant_team INT,
  created_at DATETIME,
  updated_at DATETIME
);

-- migrate:down

DROP TABLE IF EXISTS programs;