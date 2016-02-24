
# snsrv

An attempt to create a [Simplenote](http://simplenote.com/) compatible api and self hosted notes server.

## WARNING

This is currently under heavy development and is likely to be not working at all in its current state. (working on database backends right now)


## features

- aims to be 100% compatible with the simplenote third party api (this means you should be able to point your simplenote client to the address of this server and it will work out of the box)
- multiuser, secure, etc...
- scalable with mongodb (maybe - at least sqlite3, but ability to add more db backends), and flask structure

## dependencies 

The following software and libraries are used:

- python3
- python-flask
- python-urllib
- python-bcrypt
- python-jinja

(optional - for sqlite backend)

- python-sqlite


(optional - for mongodb backend) 

- python-pymongo
- mongodb


## TODO/ROADMAP

- [INPROGRESS] complete and stabilize a database backend
- [TODO] sanitize data on update and create, etc.
- [TODO] implement complete api (aiming for simplenote api v2.1.3)
- [TODO] more testing of api!
- [TODO] document the api
- [TODO] web interface for managing users
- [TODO] full web interface for interacting with notes

## running

Currently tested like this:

- clone the repository
- edit config.py to your liking
- `$ python app.py` for the development server 

## contributing

At the moment the server needs a lot of work! 
Many things must be implemented, and then thoroughly tested for compatibility, stability, and security.
If you would like to contribute, feel free to contact me, raise an issue, or submit a pull request. :)

## documentation

(OUTOFDATE - see roadmap) 
See `swagger.yaml` for the api documentation - can be viewed using a [swagger](http://swagger.io/) ui.

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
