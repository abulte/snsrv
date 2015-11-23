
# simplenote_srv

__attempt to create a fully featured server to implement the simplenote api (and be compatible with current unofficial simplenote clients)__

The following software and libraries are used:

- python3
- mongodb
- python-pymongo
- python-flask
- python-urllib

## TODO

- sanitize data on update and create
- create proper login and token system
- more testing!

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


Copyright © Samuel Walladge 2015
