#! /usr/bin/python

# Copyright (c) 2015 Samuel Walladge
# Distributed under the terms of the GNU General Public License version 3.


import os
from flask import Flask, request, Response, jsonify
from functools import wraps
from urllib.parse import parse_qs, quote, unquote
import base64
import json
import bcrypt
import random
import uuid
from pymongo import MongoClient

from notesdb import NotesDB



def check_auth(username, password):
    """This function is called to check if a username /
       password combination is valid.
       Returns True if valid, False otherwise
    """

    users_db = app.config.get('database')['users']

    user = users_db.find_one({'username': username})
    if not user:
        return False # username doesn't exist

    # check if equal to password in database
    if bcrypt.hashpw(password.encode(), user['hashed']) == user['hashed']:
        return True

    return False


def get_token(username):
    """ returns a valid token for the given user (generates new one if needed)
        currently doesn't validate user - expected to be protected by check_auth function
    """

    db = app.config.get('database')['users']
    user = db.find_one({'username': username})

    if user.get('tokenisvalid', False):
        # token is valid, return it
        return user['token']
    else:
        # else generate new one
        token = (str(uuid.uuid4())+str(uuid.uuid4())).replace('-','').upper()

        user['token'] = token
        user['tokenisvalid'] = True
        db.update({'_id': user['_id']}, user)

        return token




def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get("auth",None)
        username = request.args.get("email",None)

        # check for existance
        if username is None or token is None:
            return Response("invalid or missing credentials", 401)

        # check for user existance
        user = app.config.get('database')['users'].find_one({'username': username})
        if not user:
            return Response("invalid or missing credentials", 401)

        # check token valid. TODO: token expire time
        if user['token'] == token and user.get('tokenisvalid', False):
            # caching to avoid creating the notesdb class every time
            users_cache = app.config.get('users_cache')
            if username in users_cache:
                db = users_cache[username]
            else:
                db = NotesDB(app.config.get('database')['notes'][username])
                users_cache[username] = db
            return f(db, *args, **kwargs)

        return Response("invalid credentials", 401)

    return decorated


app = Flask(__name__)


@app.route("/api2/data/<note_id>/<int:version>")
@app.route("/api2/data/<note_id>")
@requires_auth
def get_note(user, note_id, version=None):
    note = user.get_note(note_id, version)
    if note is None:
        return Response("Cannot get: note not found",404)

    return jsonify(**note)
    #return "data endpoint - get note id:%s, version:%s" % (note_id, str(version))


@app.route("/api2/data/<note_id>", methods=['POST'])
@requires_auth
def update_note(user, note_id):
    data = request.get_data().decode(encoding='utf-8')
    if data.lstrip().startswith('%7B'): # someone urlencoded the post data :(
        data = unquote(data)

    data = json.loads(data)

    status, data = user.update_note(note_id, data)

    if status == 200:
        if data is None:
            return Response("Cannot update: unknown error",500)
        return jsonify(**data)
    return Response(data, status)
    #return "data endpoint - update note id:%s" % (note_id)


@app.route("/api2/data", methods=['POST'])
@requires_auth
def create_note(user):
    data = request.get_data().decode(encoding='utf-8')
    if data.lstrip().startswith('%7B'): # someone urlencoded the post data :(
        data = unquote(data)

    data = json.loads(data)
    status, data = user.create_note(data)

    if status == 200:
        if data is None:
            return Response("Cannot create: unknown error",500)
        return jsonify(**data)
    return Response(data, status)



@app.route("/api2/data/<note_id>", methods=['DELETE'])
@requires_auth
def delete_note(user, note_id):
    status, data = user.delete_note(note_id)

    if status == 200:
        return ""
    else:
        return Response(data, status)
    
    #return "data endpoint - delete note id:%s" % (note_id)


@app.route("/api2/index")
@requires_auth
def get_notes_list(user):

    # all info in the querystring
    length = request.args.get("length", None)
    since = request.args.get("since", None)
    mark = request.args.get("mark", None)


    status,data = user.list_notes(length, since, mark)

    if status == 200:
        return jsonify(**data)
    else:
        return Response(data, status)


@app.route('/api/login', methods=['POST'])
def login():

    # email and password given in querystring format in post data urlencoded then base64 encoded
    data = request.get_data()
    credentials = parse_qs(base64.decodestring(data).decode(encoding='UTF-8'))

    if "email" in credentials and "password" in credentials:
        email = unquote(credentials["email"][0])
        password = unquote(credentials["password"][0])
    else:
        return Response("invalid or missing credentials", 401)
    
    if check_auth(email, password):
        return get_token(email) # note this function not secured due to check_auth protecting it

    return Response("invalid credentials", 401)


if __name__ == '__main__':
    app.config.from_object('config')

    if os.environ.get('FLASK_SIMPLENOTE_SRV'):
        app.config.from_envvar('FLASK_SIMPLENOTE_SRV')

    mongo_client = MongoClient(app.config.get('MONGO_HOST'), app.config.get('MONGO_PORT'))
    app.config['mongo_client'] = mongo_client
    app.config['database'] = mongo_client[app.config.get('DATABASE_ROOT_NAME')]
    app.config['users_cache'] = {}

    app.run(
            host=app.config.get('SERVER_BIND'),
            port=app.config.get('SERVER_PORT'),
           # ssl_context = ... better to run this under another web server (eg. nginx or apache) instead of this dev server
            debug = True
            )
