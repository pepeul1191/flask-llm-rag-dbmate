-- migrate:up

CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(60),
    isbn VARCHAR(30),
    pages INTEGER,
    publication_year INTEGER,
    edition_year INTEGER,
    synopsis TEXT,
    cover_image VARCHAR(100),
    pdf VARCHAR(100),
    publisher_id INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS books;