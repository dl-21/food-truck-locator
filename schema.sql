CREATE TABLE food_trucks(
id integer primary key,
vendor varchar(100) not null,
food_items varchar(255),
address varchar(100),
latitude decimal(9,6),
longitude decimal(9,6));
