-- migrate:up

CREATE TABLE reviews (
  id SERIAL PRIMARY KEY,
  rating INTEGER,
  comment TEXT,
  review_date DATE,
  user_id INTEGER,
  book_id INTEGER
);

-- migrate:down

DROP TABLE reviews;