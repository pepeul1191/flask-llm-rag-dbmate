from diff_match_patch import diff_match_patch

dmp = diff_match_patch()
v1 = '''@startuml
entity "users" {
  * id : INTEGER
  --
  * username : VARCHAR(50)
  * email : VARCHAR(100)
  * created_at : DATETIME
}

entity "profiles" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * full_name : VARCHAR(100)
  * bio : TEXT
}

entity "posts" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * title : VARCHAR(200)
  * content : TEXT
  * created_at : DATETIME
}

users ||--|| profiles
users ||--o{ posts
@enduml
'''
v2 = '''@startuml
entity "users" {
  * id : INTEGER
  --
  * username : VARCHAR(50)
  * email : VARCHAR(100)
  * created_at : DATETIME
}

entity "profiles" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * full_name : VARCHAR(100)
  * bio : TEXT
}

entity "posts" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * title : VARCHAR(200)
  * content : TEXT
  * created_at : DATETIME
}

entity "comments" {
  * id : INTEGER
  --
  * post_id : INTEGER
  * user_id : INTEGER
  * content : TEXT
  * created_at : DATETIME
}

users ||--|| profiles
users ||--o{ posts
posts ||--o{ comments
users ||--o{ comments
@enduml
'''
diffs = dmp.diff_main(v1, v2)
dmp.diff_cleanupSemantic(diffs)

for op, text in diffs:
    if op == dmp.DIFF_INSERT:
        print(f"[+]{text}")
    elif op == dmp.DIFF_DELETE:
        print(f"[-]{text}")
    else:
        print(f"[=]{text}")