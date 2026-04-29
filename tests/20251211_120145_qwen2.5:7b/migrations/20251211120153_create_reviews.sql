-- migrate:up

CREATE TABLE reviews (
  id INTEGER AUTO_INCREMENT,
  rating INTEGER NOT NULL,
  comment TEXT,
  review_date DATETIME NOT NULL,
  user_id INTEGER NOT NULL,
  book_id INTEGER NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (book_id) REFERENCES books(id)
);

-- migrate:down

DROP TABLE IF EXISTS reviews;