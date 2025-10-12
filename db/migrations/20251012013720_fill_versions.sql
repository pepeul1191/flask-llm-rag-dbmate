-- migrate:up

-- Versiones para el Proyecto 1 (12 versiones)
INSERT INTO versions (id, name, model, created_at, updated_at, project_id) VALUES 
(1, 'v1.0-initial-schema', '@startuml
entity "users" {
  * id : INTEGER
  --
  * username : VARCHAR(50)
  * email : VARCHAR(100)
  * created_at : DATETIME
}
@enduml', '2024-01-15 09:00:00', '2024-01-15 09:00:00', 1),

(2, 'v1.1-add-profiles', '@startuml
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

users ||--|| profiles
@enduml', '2024-01-20 14:30:00', '2024-01-20 14:30:00', 1),

(3, 'v1.2-posts-system', '@startuml
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
@enduml', '2024-01-25 11:15:00', '2024-01-25 11:15:00', 1),

(4, 'v1.3-comments-feature', '@startuml
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
@enduml', '2024-02-01 16:45:00', '2024-02-01 16:45:00', 1),

(5, 'v1.4-categories-tags', '@startuml
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

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "tags" {
  * id : INTEGER
  --
  * name : VARCHAR(30)
}

entity "post_tags" {
  * post_id : INTEGER
  * tag_id : INTEGER
}

users ||--|| profiles
users ||--o{ posts
posts ||--o{ comments
users ||--o{ comments
posts }o--|| categories
posts }o--o{ tags
@enduml', '2024-02-10 10:20:00', '2024-02-10 10:20:00', 1),

(6, 'v1.5-media-attachments', '@startuml
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

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "tags" {
  * id : INTEGER
  --
  * name : VARCHAR(30)
}

entity "post_tags" {
  * post_id : INTEGER
  * tag_id : INTEGER
}

entity "media" {
  * id : INTEGER
  --
  * post_id : INTEGER
  * filename : VARCHAR(255)
  * file_type : VARCHAR(50)
  * file_size : INTEGER
}

users ||--|| profiles
users ||--o{ posts
posts ||--o{ comments
users ||--o{ comments
posts }o--|| categories
posts }o--o{ tags
posts ||--o{ media
@enduml', '2024-02-18 13:10:00', '2024-02-18 13:10:00', 1),

(7, 'v1.6-likes-system', '@startuml
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

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "tags" {
  * id : INTEGER
  --
  * name : VARCHAR(30)
}

entity "post_tags" {
  * post_id : INTEGER
  * tag_id : INTEGER
}

entity "media" {
  * id : INTEGER
  --
  * post_id : INTEGER
  * filename : VARCHAR(255)
  * file_type : VARCHAR(50)
  * file_size : INTEGER
}

entity "likes" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * post_id : INTEGER
  * created_at : DATETIME
}

users ||--|| profiles
users ||--o{ posts
posts ||--o{ comments
users ||--o{ comments
posts }o--|| categories
posts }o--o{ tags
posts ||--o{ media
users ||--o{ likes
posts ||--o{ likes
@enduml', '2024-02-25 15:30:00', '2024-02-25 15:30:00', 1),

(8, 'v2.0-notifications', '@startuml
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

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "tags" {
  * id : INTEGER
  --
  * name : VARCHAR(30)
}

entity "post_tags" {
  * post_id : INTEGER
  * tag_id : INTEGER
}

entity "media" {
  * id : INTEGER
  --
  * post_id : INTEGER
  * filename : VARCHAR(255)
  * file_type : VARCHAR(50)
  * file_size : INTEGER
}

entity "likes" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * post_id : INTEGER
  * created_at : DATETIME
}

entity "notifications" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * type : VARCHAR(50)
  * message : TEXT
  * is_read : BOOLEAN
  * created_at : DATETIME
}

users ||--|| profiles
users ||--o{ posts
posts ||--o{ comments
users ||--o{ comments
posts }o--|| categories
posts }o--o{ tags
posts ||--o{ media
users ||--o{ likes
posts ||--o{ likes
users ||--o{ notifications
@enduml', '2024-03-05 09:45:00', '2024-03-05 09:45:00', 1),

(9, 'v2.1-followers-system', '@startuml
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

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "tags" {
  * id : INTEGER
  --
  * name : VARCHAR(30)
}

entity "post_tags" {
  * post_id : INTEGER
  * tag_id : INTEGER
}

entity "media" {
  * id : INTEGER
  --
  * post_id : INTEGER
  * filename : VARCHAR(255)
  * file_type : VARCHAR(50)
  * file_size : INTEGER
}

entity "likes" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * post_id : INTEGER
  * created_at : DATETIME
}

entity "notifications" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * type : VARCHAR(50)
  * message : TEXT
  * is_read : BOOLEAN
  * created_at : DATETIME
}

entity "followers" {
  * follower_id : INTEGER
  * following_id : INTEGER
  * created_at : DATETIME
}

users ||--|| profiles
users ||--o{ posts
posts ||--o{ comments
users ||--o{ comments
posts }o--|| categories
posts }o--o{ tags
posts ||--o{ media
users ||--o{ likes
posts ||--o{ likes
users ||--o{ notifications
users }o--o{ users
@enduml', '2024-03-12 14:20:00', '2024-03-12 14:20:00', 1),

(10, 'v2.2-messages', '@startuml
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

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "tags" {
  * id : INTEGER
  --
  * name : VARCHAR(30)
}

entity "post_tags" {
  * post_id : INTEGER
  * tag_id : INTEGER
}

entity "media" {
  * id : INTEGER
  --
  * post_id : INTEGER
  * filename : VARCHAR(255)
  * file_type : VARCHAR(50)
  * file_size : INTEGER
}

entity "likes" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * post_id : INTEGER
  * created_at : DATETIME
}

entity "notifications" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * type : VARCHAR(50)
  * message : TEXT
  * is_read : BOOLEAN
  * created_at : DATETIME
}

entity "followers" {
  * follower_id : INTEGER
  * following_id : INTEGER
  * created_at : DATETIME
}

entity "messages" {
  * id : INTEGER
  --
  * sender_id : INTEGER
  * receiver_id : INTEGER
  * content : TEXT
  * is_read : BOOLEAN
  * created_at : DATETIME
}

users ||--|| profiles
users ||--o{ posts
posts ||--o{ comments
users ||--o{ comments
posts }o--|| categories
posts }o--o{ tags
posts ||--o{ media
users ||--o{ likes
posts ||--o{ likes
users ||--o{ notifications
users }o--o{ users
users ||--o{ messages
@enduml', '2024-03-20 11:00:00', '2024-03-20 11:00:00', 1),

(11, 'v2.3-settings', '@startuml
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

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "tags" {
  * id : INTEGER
  --
  * name : VARCHAR(30)
}

entity "post_tags" {
  * post_id : INTEGER
  * tag_id : INTEGER
}

entity "media" {
  * id : INTEGER
  --
  * post_id : INTEGER
  * filename : VARCHAR(255)
  * file_type : VARCHAR(50)
  * file_size : INTEGER
}

entity "likes" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * post_id : INTEGER
  * created_at : DATETIME
}

entity "notifications" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * type : VARCHAR(50)
  * message : TEXT
  * is_read : BOOLEAN
  * created_at : DATETIME
}

entity "followers" {
  * follower_id : INTEGER
  * following_id : INTEGER
  * created_at : DATETIME
}

entity "messages" {
  * id : INTEGER
  --
  * sender_id : INTEGER
  * receiver_id : INTEGER
  * content : TEXT
  * is_read : BOOLEAN
  * created_at : DATETIME
}

entity "user_settings" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * theme : VARCHAR(20)
  * notifications_enabled : BOOLEAN
  * language : VARCHAR(10)
}

users ||--|| profiles
users ||--o{ posts
posts ||--o{ comments
users ||--o{ comments
posts }o--|| categories
posts }o--o{ tags
posts ||--o{ media
users ||--o{ likes
posts ||--o{ likes
users ||--o{ notifications
users }o--o{ users
users ||--o{ messages
users ||--|| user_settings
@enduml', '2024-03-28 16:45:00', '2024-03-28 16:45:00', 1),

(12, 'v3.0-analytics', '@startuml
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

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "tags" {
  * id : INTEGER
  --
  * name : VARCHAR(30)
}

entity "post_tags" {
  * post_id : INTEGER
  * tag_id : INTEGER
}

entity "media" {
  * id : INTEGER
  --
  * post_id : INTEGER
  * filename : VARCHAR(255)
  * file_type : VARCHAR(50)
  * file_size : INTEGER
}

entity "likes" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * post_id : INTEGER
  * created_at : DATETIME
}

entity "notifications" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * type : VARCHAR(50)
  * message : TEXT
  * is_read : BOOLEAN
  * created_at : DATETIME
}

entity "followers" {
  * follower_id : INTEGER
  * following_id : INTEGER
  * created_at : DATETIME
}

entity "messages" {
  * id : INTEGER
  --
  * sender_id : INTEGER
  * receiver_id : INTEGER
  * content : TEXT
  * is_read : BOOLEAN
  * created_at : DATETIME
}

entity "user_settings" {
  * id : INTEGER
  --
  * user_id : INTEGER
  * theme : VARCHAR(20)
  * notifications_enabled : BOOLEAN
  * language : VARCHAR(10)
}

entity "analytics" {
  * id : INTEGER
  --
  * post_id : INTEGER
  * views : INTEGER
  * unique_views : INTEGER
  * date : DATE
}

users ||--|| profiles
users ||--o{ posts
posts ||--o{ comments
users ||--o{ comments
posts }o--|| categories
posts }o--o{ tags
posts ||--o{ media
users ||--o{ likes
posts ||--o{ likes
users ||--o{ notifications
users }o--o{ users
users ||--o{ messages
users ||--|| user_settings
posts ||--o{ analytics
@enduml', '2024-04-05 13:20:00', '2024-04-05 13:20:00', 1);

INSERT INTO versions (id, name, model, created_at, updated_at, project_id) VALUES 
(13, 'v1.0-ecommerce-core', '@startuml
entity "products" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * price : DECIMAL(10,2)
  * stock : INTEGER
}
@enduml', '2024-01-10 08:30:00', '2024-01-10 08:30:00', 2),

(14, 'v1.1-categories', '@startuml
entity "products" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * price : DECIMAL(10,2)
  * stock : INTEGER
}

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "product_categories" {
  * product_id : INTEGER
  * category_id : INTEGER
}

products }o--o{ categories
@enduml', '2024-01-18 10:15:00', '2024-01-18 10:15:00', 2),

(15, 'v1.2-customers', '@startuml
entity "products" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * price : DECIMAL(10,2)
  * stock : INTEGER
}

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "product_categories" {
  * product_id : INTEGER
  * category_id : INTEGER
}

entity "customers" {
  * id : INTEGER
  --
  * email : VARCHAR(100)
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * created_at : DATETIME
}

products }o--o{ categories
@enduml', '2024-01-25 14:20:00', '2024-01-25 14:20:00', 2),

(16, 'v1.3-orders-system', '@startuml
entity "products" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * price : DECIMAL(10,2)
  * stock : INTEGER
}

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "product_categories" {
  * product_id : INTEGER
  * category_id : INTEGER
}

entity "customers" {
  * id : INTEGER
  --
  * email : VARCHAR(100)
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * created_at : DATETIME
}

entity "orders" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "order_items" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * product_id : INTEGER
  * quantity : INTEGER
  * unit_price : DECIMAL(10,2)
}

products }o--o{ categories
customers ||--o{ orders
orders ||--o{ order_items
order_items }o--|| products
@enduml', '2024-02-05 09:45:00', '2024-02-05 09:45:00', 2),

(17, 'v1.4-payments', '@startuml
entity "products" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * price : DECIMAL(10,2)
  * stock : INTEGER
}

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "product_categories" {
  * product_id : INTEGER
  * category_id : INTEGER
}

entity "customers" {
  * id : INTEGER
  --
  * email : VARCHAR(100)
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * created_at : DATETIME
}

entity "orders" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "order_items" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * product_id : INTEGER
  * quantity : INTEGER
  * unit_price : DECIMAL(10,2)
}

entity "payments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * amount : DECIMAL(10,2)
  * payment_method : VARCHAR(50)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

products }o--o{ categories
customers ||--o{ orders
orders ||--o{ order_items
order_items }o--|| products
orders ||--|| payments
@enduml', '2024-02-15 11:30:00', '2024-02-15 11:30:00', 2),

(18, 'v1.5-shipping', '@startuml
entity "products" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * price : DECIMAL(10,2)
  * stock : INTEGER
}

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "product_categories" {
  * product_id : INTEGER
  * category_id : INTEGER
}

entity "customers" {
  * id : INTEGER
  --
  * email : VARCHAR(100)
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * created_at : DATETIME
}

entity "orders" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "order_items" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * product_id : INTEGER
  * quantity : INTEGER
  * unit_price : DECIMAL(10,2)
}

entity "payments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * amount : DECIMAL(10,2)
  * payment_method : VARCHAR(50)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "shipping_addresses" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * address : VARCHAR(255)
  * city : VARCHAR(50)
  * country : VARCHAR(50)
  * postal_code : VARCHAR(20)
}

entity "shipments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * shipping_address_id : INTEGER
  * carrier : VARCHAR(50)
  * tracking_number : VARCHAR(100)
  * status : VARCHAR(20)
}

products }o--o{ categories
customers ||--o{ orders
orders ||--o{ order_items
order_items }o--|| products
orders ||--|| payments
customers ||--o{ shipping_addresses
orders ||--o{ shipments
shipments }o--|| shipping_addresses
@enduml', '2024-02-25 15:10:00', '2024-02-25 15:10:00', 2),

(19, 'v2.0-reviews-ratings', '@startuml
entity "products" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * price : DECIMAL(10,2)
  * stock : INTEGER
}

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "product_categories" {
  * product_id : INTEGER
  * category_id : INTEGER
}

entity "customers" {
  * id : INTEGER
  --
  * email : VARCHAR(100)
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * created_at : DATETIME
}

entity "orders" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "order_items" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * product_id : INTEGER
  * quantity : INTEGER
  * unit_price : DECIMAL(10,2)
}

entity "payments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * amount : DECIMAL(10,2)
  * payment_method : VARCHAR(50)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "shipping_addresses" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * address : VARCHAR(255)
  * city : VARCHAR(50)
  * country : VARCHAR(50)
  * postal_code : VARCHAR(20)
}

entity "shipments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * shipping_address_id : INTEGER
  * carrier : VARCHAR(50)
  * tracking_number : VARCHAR(100)
  * status : VARCHAR(20)
}

entity "reviews" {
  * id : INTEGER
  --
  * product_id : INTEGER
  * customer_id : INTEGER
  * rating : INTEGER
  * comment : TEXT
  * created_at : DATETIME
}

products }o--o{ categories
customers ||--o{ orders
orders ||--o{ order_items
order_items }o--|| products
orders ||--|| payments
customers ||--o{ shipping_addresses
orders ||--o{ shipments
shipments }o--|| shipping_addresses
products ||--o{ reviews
customers ||--o{ reviews
@enduml', '2024-03-08 13:45:00', '2024-03-08 13:45:00', 2),

(20, 'v2.1-wishlist', '@startuml
entity "products" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * price : DECIMAL(10,2)
  * stock : INTEGER
}

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "product_categories" {
  * product_id : INTEGER
  * category_id : INTEGER
}

entity "customers" {
  * id : INTEGER
  --
  * email : VARCHAR(100)
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * created_at : DATETIME
}

entity "orders" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "order_items" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * product_id : INTEGER
  * quantity : INTEGER
  * unit_price : DECIMAL(10,2)
}

entity "payments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * amount : DECIMAL(10,2)
  * payment_method : VARCHAR(50)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "shipping_addresses" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * address : VARCHAR(255)
  * city : VARCHAR(50)
  * country : VARCHAR(50)
  * postal_code : VARCHAR(20)
}

entity "shipments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * shipping_address_id : INTEGER
  * carrier : VARCHAR(50)
  * tracking_number : VARCHAR(100)
  * status : VARCHAR(20)
}

entity "reviews" {
  * id : INTEGER
  --
  * product_id : INTEGER
  * customer_id : INTEGER
  * rating : INTEGER
  * comment : TEXT
  * created_at : DATETIME
}

entity "wishlists" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * product_id : INTEGER
  * added_at : DATETIME
}

products }o--o{ categories
customers ||--o{ orders
orders ||--o{ order_items
order_items }o--|| products
orders ||--|| payments
customers ||--o{ shipping_addresses
orders ||--o{ shipments
shipments }o--|| shipping_addresses
products ||--o{ reviews
customers ||--o{ reviews
customers ||--o{ wishlists
products ||--o{ wishlists
@enduml', '2024-03-20 10:00:00', '2024-03-20 10:00:00', 2),

(21, 'v2.2-coupons', '@startuml
entity "products" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * price : DECIMAL(10,2)
  * stock : INTEGER
}

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "product_categories" {
  * product_id : INTEGER
  * category_id : INTEGER
}

entity "customers" {
  * id : INTEGER
  --
  * email : VARCHAR(100)
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * created_at : DATETIME
}

entity "orders" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "order_items" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * product_id : INTEGER
  * quantity : INTEGER
  * unit_price : DECIMAL(10,2)
}

entity "payments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * amount : DECIMAL(10,2)
  * payment_method : VARCHAR(50)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "shipping_addresses" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * address : VARCHAR(255)
  * city : VARCHAR(50)
  * country : VARCHAR(50)
  * postal_code : VARCHAR(20)
}

entity "shipments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * shipping_address_id : INTEGER
  * carrier : VARCHAR(50)
  * tracking_number : VARCHAR(100)
  * status : VARCHAR(20)
}

entity "reviews" {
  * id : INTEGER
  --
  * product_id : INTEGER
  * customer_id : INTEGER
  * rating : INTEGER
  * comment : TEXT
  * created_at : DATETIME
}

entity "wishlists" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * product_id : INTEGER
  * added_at : DATETIME
}

entity "coupons" {
  * id : INTEGER
  --
  * code : VARCHAR(20)
  * discount_type : VARCHAR(20)
  * discount_value : DECIMAL(10,2)
  * expires_at : DATETIME
}

entity "order_coupons" {
  * order_id : INTEGER
  * coupon_id : INTEGER
  * discount_amount : DECIMAL(10,2)
}

products }o--o{ categories
customers ||--o{ orders
orders ||--o{ order_items
order_items }o--|| products
orders ||--|| payments
customers ||--o{ shipping_addresses
orders ||--o{ shipments
shipments }o--|| shipping_addresses
products ||--o{ reviews
customers ||--o{ reviews
customers ||--o{ wishlists
products ||--o{ wishlists
orders }o--|| coupons
@enduml', '2024-04-02 14:25:00', '2024-04-02 14:25:00', 2),

(22, 'v2.3-inventory', '@startuml
entity "products" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * price : DECIMAL(10,2)
  * stock : INTEGER
}

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "product_categories" {
  * product_id : INTEGER
  * category_id : INTEGER
}

entity "customers" {
  * id : INTEGER
  --
  * email : VARCHAR(100)
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * created_at : DATETIME
}

entity "orders" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "order_items" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * product_id : INTEGER
  * quantity : INTEGER
  * unit_price : DECIMAL(10,2)
}

entity "payments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * amount : DECIMAL(10,2)
  * payment_method : VARCHAR(50)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "shipping_addresses" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * address : VARCHAR(255)
  * city : VARCHAR(50)
  * country : VARCHAR(50)
  * postal_code : VARCHAR(20)
}

entity "shipments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * shipping_address_id : INTEGER
  * carrier : VARCHAR(50)
  * tracking_number : VARCHAR(100)
  * status : VARCHAR(20)
}

entity "reviews" {
  * id : INTEGER
  --
  * product_id : INTEGER
  * customer_id : INTEGER
  * rating : INTEGER
  * comment : TEXT
  * created_at : DATETIME
}

entity "wishlists" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * product_id : INTEGER
  * added_at : DATETIME
}

entity "coupons" {
  * id : INTEGER
  --
  * code : VARCHAR(20)
  * discount_type : VARCHAR(20)
  * discount_value : DECIMAL(10,2)
  * expires_at : DATETIME
}

entity "order_coupons" {
  * order_id : INTEGER
  * coupon_id : INTEGER
  * discount_amount : DECIMAL(10,2)
}

entity "inventory_logs" {
  * id : INTEGER
  --
  * product_id : INTEGER
  * change_type : VARCHAR(20)
  * quantity : INTEGER
  * reason : TEXT
  * created_at : DATETIME
}

products }o--o{ categories
customers ||--o{ orders
orders ||--o{ order_items
order_items }o--|| products
orders ||--|| payments
customers ||--o{ shipping_addresses
orders ||--o{ shipments
shipments }o--|| shipping_addresses
products ||--o{ reviews
customers ||--o{ reviews
customers ||--o{ wishlists
products ||--o{ wishlists
orders }o--|| coupons
products ||--o{ inventory_logs
@enduml', '2024-04-15 16:40:00', '2024-04-15 16:40:00', 2),

(23, 'v3.0-analytics-ecommerce', '@startuml
entity "products" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * price : DECIMAL(10,2)
  * stock : INTEGER
}

entity "categories" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
}

entity "product_categories" {
  * product_id : INTEGER
  * category_id : INTEGER
}

entity "customers" {
  * id : INTEGER
  --
  * email : VARCHAR(100)
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * created_at : DATETIME
}

entity "orders" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "order_items" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * product_id : INTEGER
  * quantity : INTEGER
  * unit_price : DECIMAL(10,2)
}

entity "payments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * amount : DECIMAL(10,2)
  * payment_method : VARCHAR(50)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "shipping_addresses" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * address : VARCHAR(255)
  * city : VARCHAR(50)
  * country : VARCHAR(50)
  * postal_code : VARCHAR(20)
}

entity "shipments" {
  * id : INTEGER
  --
  * order_id : INTEGER
  * shipping_address_id : INTEGER
  * carrier : VARCHAR(50)
  * tracking_number : VARCHAR(100)
  * status : VARCHAR(20)
}

entity "reviews" {
  * id : INTEGER
  --
  * product_id : INTEGER
  * customer_id : INTEGER
  * rating : INTEGER
  * comment : TEXT
  * created_at : DATETIME
}

entity "wishlists" {
  * id : INTEGER
  --
  * customer_id : INTEGER
  * product_id : INTEGER
  * added_at : DATETIME
}

entity "coupons" {
  * id : INTEGER
  --
  * code : VARCHAR(20)
  * discount_type : VARCHAR(20)
  * discount_value : DECIMAL(10,2)
  * expires_at : DATETIME
}

entity "order_coupons" {
  * order_id : INTEGER
  * coupon_id : INTEGER
  * discount_amount : DECIMAL(10,2)
}

entity "inventory_logs" {
  * id : INTEGER
  --
  * product_id : INTEGER
  * change_type : VARCHAR(20)
  * quantity : INTEGER
  * reason : TEXT
  * created_at : DATETIME
}

entity "sales_analytics" {
  * id : INTEGER
  --
  * product_id : INTEGER
  * date : DATE
  * units_sold : INTEGER
  * revenue : DECIMAL(10,2)
}

products }o--o{ categories
customers ||--o{ orders
orders ||--o{ order_items
order_items }o--|| products
orders ||--|| payments
customers ||--o{ shipping_addresses
orders ||--o{ shipments
shipments }o--|| shipping_addresses
products ||--o{ reviews
customers ||--o{ reviews
customers ||--o{ wishlists
products ||--o{ wishlists
orders }o--|| coupons
products ||--o{ inventory_logs
products ||--o{ sales_analytics
@enduml', '2024-04-28 12:15:00', '2024-04-28 12:15:00', 2);

-- Versiones para el Proyecto 3 (11 versiones)
INSERT INTO versions (id, name, model, created_at, updated_at, project_id) VALUES 
(24, 'v1.0-hospital-core', '@startuml
entity "patients" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * date_of_birth : DATE
  * gender : VARCHAR(10)
  * phone : VARCHAR(20)
}
@enduml', '2024-01-08 07:45:00', '2024-01-08 07:45:00', 3),

(25, 'v1.1-doctors-staff', '@startuml
entity "patients" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * date_of_birth : DATE
  * gender : VARCHAR(10)
  * phone : VARCHAR(20)
}

entity "doctors" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * specialization : VARCHAR(50)
  * license_number : VARCHAR(20)
  * phone : VARCHAR(20)
}

entity "nurses" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * license_number : VARCHAR(20)
  * department : VARCHAR(50)
}
@enduml', '2024-01-16 09:20:00', '2024-01-16 09:20:00', 3),

(26, 'v1.2-appointments', '@startuml
entity "patients" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * date_of_birth : DATE
  * gender : VARCHAR(10)
  * phone : VARCHAR(20)
}

entity "doctors" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * specialization : VARCHAR(50)
  * license_number : VARCHAR(20)
  * phone : VARCHAR(20)
}

entity "nurses" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * license_number : VARCHAR(20)
  * department : VARCHAR(50)
}

entity "appointments" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * appointment_date : DATETIME
  * status : VARCHAR(20)
  * reason : TEXT
}

patients ||--o{ appointments
doctors ||--o{ appointments
@enduml', '2024-01-24 11:30:00', '2024-01-24 11:30:00', 3),

(27, 'v1.3-medical-records', '@startuml
entity "patients" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * date_of_birth : DATE
  * gender : VARCHAR(10)
  * phone : VARCHAR(20)
}

entity "doctors" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * specialization : VARCHAR(50)
  * license_number : VARCHAR(20)
  * phone : VARCHAR(20)
}

entity "nurses" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * license_number : VARCHAR(20)
  * department : VARCHAR(50)
}

entity "appointments" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * appointment_date : DATETIME
  * status : VARCHAR(20)
  * reason : TEXT
}

entity "medical_records" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * diagnosis : TEXT
  * treatment : TEXT
  * visit_date : DATETIME
  * notes : TEXT
}

patients ||--o{ appointments
doctors ||--o{ appointments
patients ||--o{ medical_records
doctors ||--o{ medical_records
@enduml', '2024-02-02 14:15:00', '2024-02-02 14:15:00', 3),

(28, 'v1.4-prescriptions', '@startuml
entity "patients" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * date_of_birth : DATE
  * gender : VARCHAR(10)
  * phone : VARCHAR(20)
}

entity "doctors" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * specialization : VARCHAR(50)
  * license_number : VARCHAR(20)
  * phone : VARCHAR(20)
}

entity "nurses" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * license_number : VARCHAR(20)
  * department : VARCHAR(50)
}

entity "appointments" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * appointment_date : DATETIME
  * status : VARCHAR(20)
  * reason : TEXT
}

entity "medical_records" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * diagnosis : TEXT
  * treatment : TEXT
  * visit_date : DATETIME
  * notes : TEXT
}

entity "medications" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * dosage : VARCHAR(50)
}

entity "prescriptions" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * medication_id : INTEGER
  * dosage : VARCHAR(50)
  * frequency : VARCHAR(50)
  * duration : VARCHAR(50)
  * prescribed_date : DATETIME
}

patients ||--o{ appointments
doctors ||--o{ appointments
patients ||--o{ medical_records
doctors ||--o{ medical_records
patients ||--o{ prescriptions
doctors ||--o{ prescriptions
prescriptions }o--|| medications
@enduml', '2024-02-12 10:45:00', '2024-02-12 10:45:00', 3),

(29, 'v1.5-laboratory', '@startuml
entity "patients" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * date_of_birth : DATE
  * gender : VARCHAR(10)
  * phone : VARCHAR(20)
}

entity "doctors" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * specialization : VARCHAR(50)
  * license_number : VARCHAR(20)
  * phone : VARCHAR(20)
}

entity "nurses" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * license_number : VARCHAR(20)
  * department : VARCHAR(50)
}

entity "appointments" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * appointment_date : DATETIME
  * status : VARCHAR(20)
  * reason : TEXT
}

entity "medical_records" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * diagnosis : TEXT
  * treatment : TEXT
  * visit_date : DATETIME
  * notes : TEXT
}

entity "medications" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * dosage : VARCHAR(50)
}

entity "prescriptions" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * medication_id : INTEGER
  * dosage : VARCHAR(50)
  * frequency : VARCHAR(50)
  * duration : VARCHAR(50)
  * prescribed_date : DATETIME
}

entity "lab_tests" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * normal_range : VARCHAR(100)
}

entity "lab_results" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * test_id : INTEGER
  * result_value : VARCHAR(100)
  * result_date : DATETIME
  * interpreted_by : INTEGER
}

patients ||--o{ appointments
doctors ||--o{ appointments
patients ||--o{ medical_records
doctors ||--o{ medical_records
patients ||--o{ prescriptions
doctors ||--o{ prescriptions
prescriptions }o--|| medications
patients ||--o{ lab_results
lab_results }o--|| lab_tests
doctors ||--o{ lab_results
@enduml', '2024-02-22 13:20:00', '2024-02-22 13:20:00', 3),

(30, 'v2.0-billing', '@startuml
entity "patients" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * date_of_birth : DATE
  * gender : VARCHAR(10)
  * phone : VARCHAR(20)
}

entity "doctors" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * specialization : VARCHAR(50)
  * license_number : VARCHAR(20)
  * phone : VARCHAR(20)
}

entity "nurses" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * license_number : VARCHAR(20)
  * department : VARCHAR(50)
}

entity "appointments" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * appointment_date : DATETIME
  * status : VARCHAR(20)
  * reason : TEXT
}

entity "medical_records" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * diagnosis : TEXT
  * treatment : TEXT
  * visit_date : DATETIME
  * notes : TEXT
}

entity "medications" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * dosage : VARCHAR(50)
}

entity "prescriptions" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * medication_id : INTEGER
  * dosage : VARCHAR(50)
  * frequency : VARCHAR(50)
  * duration : VARCHAR(50)
  * prescribed_date : DATETIME
}

entity "lab_tests" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * normal_range : VARCHAR(100)
}

entity "lab_results" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * test_id : INTEGER
  * result_value : VARCHAR(100)
  * result_date : DATETIME
  * interpreted_by : INTEGER
}

entity "billing" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * appointment_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * insurance_covered : DECIMAL(10,2)
  * patient_responsibility : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "billing_items" {
  * id : INTEGER
  --
  * billing_id : INTEGER
  * item_type : VARCHAR(50)
  * item_description : VARCHAR(200)
  * amount : DECIMAL(10,2)
}

patients ||--o{ appointments
doctors ||--o{ appointments
patients ||--o{ medical_records
doctors ||--o{ medical_records
patients ||--o{ prescriptions
doctors ||--o{ prescriptions
prescriptions }o--|| medications
patients ||--o{ lab_results
lab_results }o--|| lab_tests
doctors ||--o{ lab_results
patients ||--o{ billing
appointments ||--o{ billing
billing ||--o{ billing_items
@enduml', '2024-03-06 15:30:00', '2024-03-06 15:30:00', 3),

(31, 'v2.1-insurance', '@startuml
entity "patients" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * date_of_birth : DATE
  * gender : VARCHAR(10)
  * phone : VARCHAR(20)
}

entity "doctors" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * specialization : VARCHAR(50)
  * license_number : VARCHAR(20)
  * phone : VARCHAR(20)
}

entity "nurses" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * license_number : VARCHAR(20)
  * department : VARCHAR(50)
}

entity "appointments" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * appointment_date : DATETIME
  * status : VARCHAR(20)
  * reason : TEXT
}

entity "medical_records" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * diagnosis : TEXT
  * treatment : TEXT
  * visit_date : DATETIME
  * notes : TEXT
}

entity "medications" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * dosage : VARCHAR(50)
}

entity "prescriptions" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * medication_id : INTEGER
  * dosage : VARCHAR(50)
  * frequency : VARCHAR(50)
  * duration : VARCHAR(50)
  * prescribed_date : DATETIME
}

entity "lab_tests" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * normal_range : VARCHAR(100)
}

entity "lab_results" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * test_id : INTEGER
  * result_value : VARCHAR(100)
  * result_date : DATETIME
  * interpreted_by : INTEGER
}

entity "billing" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * appointment_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * insurance_covered : DECIMAL(10,2)
  * patient_responsibility : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "billing_items" {
  * id : INTEGER
  --
  * billing_id : INTEGER
  * item_type : VARCHAR(50)
  * item_description : VARCHAR(200)
  * amount : DECIMAL(10,2)
}

entity "insurance_companies" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * phone : VARCHAR(20)
  * address : VARCHAR(255)
}

entity "insurance_policies" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * insurance_company_id : INTEGER
  * policy_number : VARCHAR(50)
  * group_number : VARCHAR(50)
  * effective_date : DATE
  * expiration_date : DATE
}

patients ||--o{ appointments
doctors ||--o{ appointments
patients ||--o{ medical_records
doctors ||--o{ medical_records
patients ||--o{ prescriptions
doctors ||--o{ prescriptions
prescriptions }o--|| medications
patients ||--o{ lab_results
lab_results }o--|| lab_tests
doctors ||--o{ lab_results
patients ||--o{ billing
appointments ||--o{ billing
billing ||--o{ billing_items
patients ||--o{ insurance_policies
insurance_policies }o--|| insurance_companies
@enduml', '2024-03-18 12:10:00', '2024-03-18 12:10:00', 3),

(32, 'v2.2-departments-wards', '@startuml
entity "patients" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * date_of_birth : DATE
  * gender : VARCHAR(10)
  * phone : VARCHAR(20)
}

entity "doctors" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * specialization : VARCHAR(50)
  * license_number : VARCHAR(20)
  * phone : VARCHAR(20)
}

entity "nurses" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * license_number : VARCHAR(20)
  * department : VARCHAR(50)
}

entity "appointments" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * appointment_date : DATETIME
  * status : VARCHAR(20)
  * reason : TEXT
}

entity "medical_records" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * diagnosis : TEXT
  * treatment : TEXT
  * visit_date : DATETIME
  * notes : TEXT
}

entity "medications" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * dosage : VARCHAR(50)
}

entity "prescriptions" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * medication_id : INTEGER
  * dosage : VARCHAR(50)
  * frequency : VARCHAR(50)
  * duration : VARCHAR(50)
  * prescribed_date : DATETIME
}

entity "lab_tests" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * normal_range : VARCHAR(100)
}

entity "lab_results" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * test_id : INTEGER
  * result_value : VARCHAR(100)
  * result_date : DATETIME
  * interpreted_by : INTEGER
}

entity "billing" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * appointment_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * insurance_covered : DECIMAL(10,2)
  * patient_responsibility : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "billing_items" {
  * id : INTEGER
  --
  * billing_id : INTEGER
  * item_type : VARCHAR(50)
  * item_description : VARCHAR(200)
  * amount : DECIMAL(10,2)
}

entity "insurance_companies" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * phone : VARCHAR(20)
  * address : VARCHAR(255)
}

entity "insurance_policies" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * insurance_company_id : INTEGER
  * policy_number : VARCHAR(50)
  * group_number : VARCHAR(50)
  * effective_date : DATE
  * expiration_date : DATE
}

entity "departments" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
  * head_doctor_id : INTEGER
}

entity "wards" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * department_id : INTEGER
  * capacity : INTEGER
  * current_occupancy : INTEGER
}

entity "admissions" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * ward_id : INTEGER
  * admission_date : DATETIME
  * discharge_date : DATETIME
  * status : VARCHAR(20)
}

patients ||--o{ appointments
doctors ||--o{ appointments
patients ||--o{ medical_records
doctors ||--o{ medical_records
patients ||--o{ prescriptions
doctors ||--o{ prescriptions
prescriptions }o--|| medications
patients ||--o{ lab_results
lab_results }o--|| lab_tests
doctors ||--o{ lab_results
patients ||--o{ billing
appointments ||--o{ billing
billing ||--o{ billing_items
patients ||--o{ insurance_policies
insurance_policies }o--|| insurance_companies
doctors }o--|| departments
wards }o--|| departments
patients ||--o{ admissions
admissions }o--|| wards
@enduml', '2024-03-30 08:50:00', '2024-03-30 08:50:00', 3),

(33, 'v2.3-emergency', '@startuml
entity "patients" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * date_of_birth : DATE
  * gender : VARCHAR(10)
  * phone : VARCHAR(20)
}

entity "doctors" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * specialization : VARCHAR(50)
  * license_number : VARCHAR(20)
  * phone : VARCHAR(20)
}

entity "nurses" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * license_number : VARCHAR(20)
  * department : VARCHAR(50)
}

entity "appointments" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * appointment_date : DATETIME
  * status : VARCHAR(20)
  * reason : TEXT
}

entity "medical_records" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * diagnosis : TEXT
  * treatment : TEXT
  * visit_date : DATETIME
  * notes : TEXT
}

entity "medications" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * dosage : VARCHAR(50)
}

entity "prescriptions" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * medication_id : INTEGER
  * dosage : VARCHAR(50)
  * frequency : VARCHAR(50)
  * duration : VARCHAR(50)
  * prescribed_date : DATETIME
}

entity "lab_tests" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * normal_range : VARCHAR(100)
}

entity "lab_results" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * test_id : INTEGER
  * result_value : VARCHAR(100)
  * result_date : DATETIME
  * interpreted_by : INTEGER
}

entity "billing" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * appointment_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * insurance_covered : DECIMAL(10,2)
  * patient_responsibility : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "billing_items" {
  * id : INTEGER
  --
  * billing_id : INTEGER
  * item_type : VARCHAR(50)
  * item_description : VARCHAR(200)
  * amount : DECIMAL(10,2)
}

entity "insurance_companies" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * phone : VARCHAR(20)
  * address : VARCHAR(255)
}

entity "insurance_policies" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * insurance_company_id : INTEGER
  * policy_number : VARCHAR(50)
  * group_number : VARCHAR(50)
  * effective_date : DATE
  * expiration_date : DATE
}

entity "departments" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
  * head_doctor_id : INTEGER
}

entity "wards" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * department_id : INTEGER
  * capacity : INTEGER
  * current_occupancy : INTEGER
}

entity "admissions" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * ward_id : INTEGER
  * admission_date : DATETIME
  * discharge_date : DATETIME
  * status : VARCHAR(20)
}

entity "emergency_cases" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * triage_level : VARCHAR(20)
  * chief_complaint : TEXT
  * arrival_time : DATETIME
  * disposition : VARCHAR(50)
  * disposition_time : DATETIME
}

patients ||--o{ appointments
doctors ||--o{ appointments
patients ||--o{ medical_records
doctors ||--o{ medical_records
patients ||--o{ prescriptions
doctors ||--o{ prescriptions
prescriptions }o--|| medications
patients ||--o{ lab_results
lab_results }o--|| lab_tests
doctors ||--o{ lab_results
patients ||--o{ billing
appointments ||--o{ billing
billing ||--o{ billing_items
patients ||--o{ insurance_policies
insurance_policies }o--|| insurance_companies
doctors }o--|| departments
wards }o--|| departments
patients ||--o{ admissions
admissions }o--|| wards
patients ||--o{ emergency_cases
@enduml', '2024-04-12 16:25:00', '2024-04-12 16:25:00', 3),

(34, 'v3.0-analytics-healthcare', '@startuml
entity "patients" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * date_of_birth : DATE
  * gender : VARCHAR(10)
  * phone : VARCHAR(20)
}

entity "doctors" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * specialization : VARCHAR(50)
  * license_number : VARCHAR(20)
  * phone : VARCHAR(20)
}

entity "nurses" {
  * id : INTEGER
  --
  * first_name : VARCHAR(50)
  * last_name : VARCHAR(50)
  * license_number : VARCHAR(20)
  * department : VARCHAR(50)
}

entity "appointments" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * appointment_date : DATETIME
  * status : VARCHAR(20)
  * reason : TEXT
}

entity "medical_records" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * diagnosis : TEXT
  * treatment : TEXT
  * visit_date : DATETIME
  * notes : TEXT
}

entity "medications" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * dosage : VARCHAR(50)
}

entity "prescriptions" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * doctor_id : INTEGER
  * medication_id : INTEGER
  * dosage : VARCHAR(50)
  * frequency : VARCHAR(50)
  * duration : VARCHAR(50)
  * prescribed_date : DATETIME
}

entity "lab_tests" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * description : TEXT
  * normal_range : VARCHAR(100)
}

entity "lab_results" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * test_id : INTEGER
  * result_value : VARCHAR(100)
  * result_date : DATETIME
  * interpreted_by : INTEGER
}

entity "billing" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * appointment_id : INTEGER
  * total_amount : DECIMAL(10,2)
  * insurance_covered : DECIMAL(10,2)
  * patient_responsibility : DECIMAL(10,2)
  * status : VARCHAR(20)
  * created_at : DATETIME
}

entity "billing_items" {
  * id : INTEGER
  --
  * billing_id : INTEGER
  * item_type : VARCHAR(50)
  * item_description : VARCHAR(200)
  * amount : DECIMAL(10,2)
}

entity "insurance_companies" {
  * id : INTEGER
  --
  * name : VARCHAR(100)
  * phone : VARCHAR(20)
  * address : VARCHAR(255)
}

entity "insurance_policies" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * insurance_company_id : INTEGER
  * policy_number : VARCHAR(50)
  * group_number : VARCHAR(50)
  * effective_date : DATE
  * expiration_date : DATE
}

entity "departments" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * description : TEXT
  * head_doctor_id : INTEGER
}

entity "wards" {
  * id : INTEGER
  --
  * name : VARCHAR(50)
  * department_id : INTEGER
  * capacity : INTEGER
  * current_occupancy : INTEGER
}

entity "admissions" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * ward_id : INTEGER
  * admission_date : DATETIME
  * discharge_date : DATETIME
  * status : VARCHAR(20)
}

entity "emergency_cases" {
  * id : INTEGER
  --
  * patient_id : INTEGER
  * triage_level : VARCHAR(20)
  * chief_complaint : TEXT
  * arrival_time : DATETIME
  * disposition : VARCHAR(50)
  * disposition_time : DATETIME
}

entity "healthcare_analytics" {
  * id : INTEGER
  --
  * date : DATE
  * department_id : INTEGER
  * total_patients : INTEGER
  * total_appointments : INTEGER
  * average_wait_time : INTEGER
  * revenue : DECIMAL(10,2)
}

patients ||--o{ appointments
doctors ||--o{ appointments
patients ||--o{ medical_records
doctors ||--o{ medical_records
patients ||--o{ prescriptions
doctors ||--o{ prescriptions
prescriptions }o--|| medications
patients ||--o{ lab_results
lab_results }o--|| lab_tests
doctors ||--o{ lab_results
patients ||--o{ billing
appointments ||--o{ billing
billing ||--o{ billing_items
patients ||--o{ insurance_policies
insurance_policies }o--|| insurance_companies
doctors }o--|| departments
wards }o--|| departments
patients ||--o{ admissions
admissions }o--|| wards
patients ||--o{ emergency_cases
departments ||--o{ healthcare_analytics
@enduml', '2024-04-25 11:35:00', '2024-04-25 11:35:00', 3);

-- migrate:down

DELETE FROM versions;