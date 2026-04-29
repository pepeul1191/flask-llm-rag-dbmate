-- migrate:up

CREATE TABLE reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rating INTEGER NOT NULL,
  comment TEXT NOT NULL,
  review_date DATETIME NOT NULL,
  user_id INTEGER NOT NULL,
  book_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (book_id) REFERENCES books(id)
);

-- migrate:down

DROP TABLE reviews;