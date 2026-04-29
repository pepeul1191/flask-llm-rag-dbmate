-- migrate:up

CREATE TABLE reviews ( id SERIAL PRIMARY KEY, rating INTEGER NOT NULL, comment TEXT, review_date TIMESTAMP WITH TIME ZONE, user_id INTEGER REFERENCES users(id), book_id INTEGER REFERENCES books(id) );

-- migrate:down

DROP TABLE IF EXISTS REVIEWS;