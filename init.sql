
-- init the sqlite database

create table if not exists users 
(
  userid int primary key not null,
  email  text not null,
  hashed text not null
)

-- create table notes if not exists
-- (
--   ... TODO
--
