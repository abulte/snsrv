
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
  key text not null,
  userid integer not null,
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

  primary key (key),
  foreign key (userid) references users(id)
);

create table if not exists versions
(
  key text not null,
  versiondate numeric, -- seconds since epoch
  content text,
  version integer not null,

  primary key (key, version),
  foreign key (key) references notes(key)
);

create table if not exists tags
(
  id integer not null,
  _index integer not null,
  name text not null,
  lower_name text not null,
  version integer,

  primary key (id),
  unique (lower_name),
  unique (name)
);

create table if not exists tagged
(
  notekey not null,
  tagid not null,

  foreign key (notekey) references notes(key),
  foreign key (tagid) references tags(id),

  primary key (notekey, tagid)
);

-- sample db stuff -- remove when in production!
-- username: sam, password: aoeuaoeu
INSERT INTO users select 1,'sam',X'243262243132246B72543036492F68355754504C324137732E314570754F595037666B624E333268682F6641726A732F6C5647547935372F79346832',NULL,NULL where not exists (select * from users where email = 'sam');

insert into notes select 'abc', 1,  0, 1456325139.593469, 1456325139.593469, 1, 1, 1, null, null, 'hi there!', 0, null, 1, 0 where not exists (select * from notes where key = 'abc');

insert into tags select 1, 1, 'Tag1', 'tag1', 1 where not exists (select * from tags where id = 1);
insert into tagged select 'abc', 1 where not exists (select * from tagged where notekey = 'abc' and tagid = 1);

