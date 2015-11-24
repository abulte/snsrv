
# simplenote_srv

__attempt to create a SimpleNote server clone (at least the api part)__

## features

- aims to be 100% compatible with simplenote api (this means you should be able to point your simplenote client to the address of this server and it will work out of the box)
- multiuser, secure, etc...
- scalable with mongodb, and flask structure

## dependencies 

The following software and libraries are used:

- python3
- mongodb
- python-pymongo
- python-flask
- python-urllib
- python-bcrypt

## TODO

- sanitize data on update and create
- more testing!
- find more info on api to fix any potential issues (be more compatible)

## complete note structure for reference (from simplenote.py docs)

```
{
  key       : (string, note identifier, created by server),
  deleted   : (bool, whether or not note is in trash),
  modifydate: (last modified date, in seconds since epoch),
  createdate: (note created date, in seconds since epoch),
  syncnum   : (integer, number set by server, track note changes),
  version   : (integer, number set by server, track note content changes),
  minversion: (integer, number set by server, minimum version available for note),
  sharekey  : (string, shared note identifier),
  publishkey: (string, published note identifier),
  systemtags: [(Array of strings, some set by server)],
  tags      : [(Array of strings)],
  content   : (string, data content)
}
```


Copyright © 2015 Samuel Walladge
