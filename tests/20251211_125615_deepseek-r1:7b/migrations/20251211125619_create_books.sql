-- migrate:up

CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(60) NOT NULL,
    isbn VARCHAR(30) UNIQUE NOT NULL,
    pages INTEGER NOT NULL CHECK (pages > 0),
    publication_year INTEGER NOT NULL,
    edition_year INTEGER DEFAULT CURRENTYEAR() AS "edition year",
    synopsis TEXT,
    cover_image VARCHAR(100),
    pdf VARCHAR(100),
    publisher_id INTEGER NOT NULL REFERENCES publishers(id)
);

-- migrate:down

DROP TABLE IF EXISTS books;