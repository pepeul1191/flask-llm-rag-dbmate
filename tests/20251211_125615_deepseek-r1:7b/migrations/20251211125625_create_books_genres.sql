-- migrate:up

CREATE TABLE books_genres (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id),
    genre_id INTEGER NOT NULL REFERENCES genres(id)
);

-- migrate:down

DROP TABLE IF EXISTS books_genres;