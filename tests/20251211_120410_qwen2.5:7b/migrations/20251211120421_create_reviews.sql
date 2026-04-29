-- migrate:up

CREATE TABLE reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rating INTEGER,
  comment TEXT,
  review_date DATETIME,
  user_id INTEGER,
  book_id INTEGER,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (book_id) REFERENCES books(id)
);

-- migrate:down

DROP TABLE IF EXISTS reviews;