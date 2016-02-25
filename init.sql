
-- init the sqlite database

create table if not exists users 
(
  id integer not null,
  email  text not null,
  hashed text not null,
  token text,
  tokendate numeric, -- seconds since epoch
  unique (email),
  primary key (id)
);

create table if not exists notes 
(
  id integer not null,
  userid integer not null,
  key text not null,
  deleted integer,  -- should be 0 or 1
  modifydate numeric, -- seconds since epoch
  createdate numeric, -- seconds since epoch
  syncnum integer,
  version integer,
  minversion integer,
  publishkey text,
  sharekey text,
  content text,
  -- system tags
  pinned integer,
  unread integer,
  markdown integer,
  list integer,

  primary key (id),
  unique (key),
  foreign key (userid) references users(id)
);


-- sample db stuff -- remove when in production!
-- username: sam, password: aoeuaoeu
INSERT INTO users select 1,'sam',X'243262243132246B72543036492F68355754504C324137732E314570754F595037666B624E333268682F6641726A732F6C5647547935372F79346832',NULL,NULL where not exists (select * from users where email = 'sam');

insert into notes select 1, 1, 'abc', 0, 1456325139.593469, 1456325139.593469, 1, 1, 1, null, null, 'hi there!', 0, null, 1, 0 where not exists (select * from notes where key = 'abc');

