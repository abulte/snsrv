
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

## License

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


Copyright © 2015 Samuel Walladge
