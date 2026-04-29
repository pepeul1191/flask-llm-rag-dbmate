-- migrate:up

CREATE TABLE users(id INT PRIMARY KEY), NOT REPLACING THE PLACEHOLDERS WITH COLUMNS).
2. All statements must end with semicolon, use ON UPDATE CURRENT_TIMESTAMP if the column is updated at a specific time each row update (e.g.: lastUpdated TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL) and include default values where appropriate in your SQL code generation process for table creation statement(s).
3. Include 'NOT NULL' constraints wherever required fields are expected to be filled out by the user, such as email (VARCHAR), password hash VARCHAR etc., using ONLY those columns that require this constraint when creating a new record or updating an existing one in your SQL code generation process for table creation statement(s).
4. Use REAL syntax and not pseudo-code where possible to ensure compatibility with the database you are working on (MySQL, PostgreSQL) as different databases have slightly不同的 commands/statements used during migration processes of a schema or data population script like Flyway in Java ORM tools for example. 
5. Output must be directly executable SQL code within your chosen DBMS such as MySQL Workbench / pgAdmin etc., not placeholders (e.g.: SELECT id FROM users WHERE username = 'JohnDoe' NOT REPLACING THE PLACEHOLDERS WITH VALUES).  
6. Always ensure that the generated scripts are compatible with existing database schema and data, otherwise it may lead to errors or inconsistencies during migration process of your application/database system (such as missing foreign key constraints etc.).  This is why you should always use actual column names when generating SQL for a table creation statement(s).
;

-- migrate:down

DROP TABLE IF EXISTS users;