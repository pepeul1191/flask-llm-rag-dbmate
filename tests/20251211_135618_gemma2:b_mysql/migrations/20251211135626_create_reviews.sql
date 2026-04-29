-- migrate:up

CREATE TABLE reviews (
  id INT PRIMARY KEY AUTO_INCREMENT,
  rating INT NOT NULL,
  comment TEXT,
  review_date DATETIME NOT NULL,
  user_id INT FOREIGN KEY REFERENCES users(id),
  book_id INT FOREIGN KEY REFERENCES books(id)
);

-- migrate:down

DROP TABLE IF EXISTS reviews;