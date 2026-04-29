-- migrate:up

CREATE TABLE reviews (
  id INT PRIMARY KEY AUTO_INCREMENT,
  rating INT,
  comment TEXT,
  review_date DATETIME,
  user_id INT,
  book_id INT,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (book_id) REFERENCES books(id)
);

-- migrate:down

DROP TABLE reviews;