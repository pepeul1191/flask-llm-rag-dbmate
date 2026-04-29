-- migrate:up

CREATE TABLE books_authors (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id),
    author_id INTEGER NOT NULL REFERENCES authors(id)
);

-- migrate:down

DROP TABLE IF EXISTS books_authors;