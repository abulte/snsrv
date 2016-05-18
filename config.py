
# edit this config to configure your server
# all flask builtin variables will work (http://flask.pocoo.org/docs/0.10/config/)

# server bind address
# 0.0.0.0 allows connections from anywhere
SERVER_BIND = '0.0.0.0'

# and port
SERVER_PORT = 5000

# debugging mode
# WARNING: change to False in production servers
DEBUG = True

SECRET_KEY = 'nothing'

# the db backend to use - currently only sqlite ('sqlite_db')
DB_TYPE = 'sqlite_db'

# options to pass to the db backend
# below for sqlite
DB_OPTIONS = {
    'FILE': 'sqlite.db',
    'INIT_SQL_FILE': 'init.sql'
}

## example for mongodb
# DB_OPTIONS = {
#         'HOST': 'localhost',
#         'PORT': 3545
#         'DATABASE_ROOT': 'simplenote' # the database root to use
#         }




# after reading config from this file, will read from the file given in 'FLASK_SIMPLENOTE_SRV' envvar

