
# snsrv

A [Simplenote](http://simplenote.com/) compatible api and self hosted notes server.

## WARNING

This is currently under heavy development and not all features are implemented yet.


## features

- aims to be 100% compatible with the simplenote third party api (this means you should be able to point your simplenote client to the address of this server and it will work out of the box)
- multiuser, secure, etc...
- selfhosted!!
- scalable with flask structure and options for implemented database backend with scalable databases (currently only sqlite3 backend implemented)
- web interface (TODO)

## dependencies 

The following software and libraries are used:

- python3
- python-flask
- python-bcrypt
- python-sqlite

These can be installed with your package manager, or with pip once python is installed.


## running

For running/testing with the flask dev server, you can simply do the following:

1. clone the repo

2. edit config.py to suit

3. install deps and run!

```
pyvenv env
source env/bin/activate
pip install -r requirements.txt
python app.py
```

## TODO/ROADMAP

- [ALMOST] complete and stabilize a database backend 
           (almost complete using sqlite3 - probably not very well optimised though)
- [ALMOST] sanitize data on update and create, etc.
- [ALMOST - just tags api to go] implement complete api (aiming for simplenote api v2.1.3)
- [TODO] implement note sharing
- [TODO] more testing of api! (now fairly stable based on testing with [sncli](https://github.com/swalladge/sncli))
- [TODO] document the api
- [TODO] web interface for managing users
- [TODO] full web interface for interacting with notes


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


Copyright © 2015-2016 Samuel Walladge
