-- migrate:up

CREATE TABLE reviews (
  id SERIAL PRIMARY KEY,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  user_id INTEGER REFERENCES users(id),
  book_id INTEGER REFERENCES books(id)
);

-- migrate:down

DROP TABLE reviews;