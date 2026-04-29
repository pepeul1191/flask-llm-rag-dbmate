-- migrate:up

CREATE TABLE reviews (
  id INT PRIMARY KEY AUTO_INCREMENT,
  rating INTEGER NOT NULL,
  comment TEXT NOT NULL,
  review_date DATETIME NOT NULL,
  user_id INT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- migrate:down

DROP TABLE IF EXISTS reviews;