-- migrate:up

CREATE TABLE books ( id SERIAL PRIMARY KEY, title VARCHAR(60) NOT NULL, isbn VARCHAR(30) UNIQUE NOT NULL, pages INTEGER NOT NULL, publication_year INTEGER, edition_year INTEGER, synopsis TEXT, cover_image VARCHAR(100), pdf VARCHAR(100), publisher_id INTEGER REFERENCES publishers(id) );

-- migrate:down

DROP TABLE IF EXISTS BOOKS;