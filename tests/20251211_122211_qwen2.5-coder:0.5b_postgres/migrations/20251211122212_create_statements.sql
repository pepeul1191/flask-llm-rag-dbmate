-- migrate:up

CREATE TABLE statements for the specified database entities, you can use a script that iterates over each entity and constructs the necessary SQL commands. Here's a Python script that accomplishes this:

```python
import psycopg2

# Database connection parameters
db_host = 'localhost'
db_name = 'your_database_name'
db_user = 'your_username'
db_password = 'your_password'

# Create a connection to the database
conn = psycopg2.connect(
    host=db_host,
    dbname=db_name,
    user=db_user,
    password=db_password
)

# Create a cursor object using the connection
cur = conn.cursor()

# List of entities to create
entities = [
    ('users', 'id INTEGER PRIMARY KEY, username VARCHAR(30)'),
    ('countries', 'id INTEGER PRIMARY KEY, name VARCHAR(30)'),
    ('devices', 'id INTEGER PRIMARY KEY, brand VARCHAR(30)')
]

# Create CREATE TABLE statements for each entity
create_statements = []
for entity_name, column_definitions in entities:
    create_statement = f"""
    CREATE TABLE {entity_name} (
        id SERIAL PRIMARY KEY,
        {column_definitions}
    );

-- migrate:down

DROP TABLE IF EXISTS statements;