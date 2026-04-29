-- migrate:up

CREATE TABLE` statements for the specified entities, you can use a script that iterates over each entity and generates the corresponding `CREATE TABLE` statement. Here's how you can do it:

```sql
-- Create the 'users' table
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username VARCHAR(20)
);

-- migrate:down

DROP TABLE IF EXISTS users;