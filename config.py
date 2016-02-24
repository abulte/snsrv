
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


# the mongodb database name to use
DATABASE_ROOT_NAME = 'simplenote1'

# mongodb server info
MONGO_HOST = 'localhost'
MONGO_PORT = 27017



# after reading config from this file, will read from the file given in 'FLASK_SIMPLENOTE_SRV' envvar

