-- migrate:up

CREATE TABLE books_genres ( id SERIAL PRIMARY KEY, book_id INTEGER REFERENCES books(id), genre_id INTEGER REFERENCES genres(id) );

-- migrate:down

DROP TABLE IF EXISTS BOOKS_GENRES;