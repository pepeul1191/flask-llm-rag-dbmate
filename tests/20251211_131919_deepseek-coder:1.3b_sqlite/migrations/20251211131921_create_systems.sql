-- migrate:up

CREATE TABLE If NOT Exists Systems(
     id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL ,
    description  Text Not Null,  
	repository text not null,     
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,      
updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP);

-- migrate:down

DROP TABLE IF EXISTS Systems;