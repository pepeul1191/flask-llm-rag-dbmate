-- migrate:up

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rating INTEGER,
    comment TEXT,
    review_date DATETIME,
    user_id INTEGER,
    book_id INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS reviews;