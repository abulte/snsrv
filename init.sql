
-- init the sqlite database

create table if not exists users 
(
  id int not null,
  email  text not null,
  hashed text not null,

  primary key (id),
  unique (email)
);

create table if not exists notes 
(
  id int not null,
  key text not null,
  deleted integer,  -- should be 0 or 1
  modifydate numeric, -- seconds since epoch
  createdate numeric, -- seconds since epoch
  syncnum integer,
  minversion integer,
  publishkey text,
  content text,

  primary key (id),
  unique (key)
)




