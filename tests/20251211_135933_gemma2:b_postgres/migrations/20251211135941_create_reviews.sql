-- migrate:up

CREATE TABLE reviews (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  rating INTEGER NOT NULL,
  comment TEXT NOT NULL,
  review_date DATETIME NOT NULL,
  user_id INTEGER NOT NULL,
  book_id INTEGER NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS reviews;