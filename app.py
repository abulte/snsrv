#! /usr/bin/python

# Copyright (c) 2015 Samuel Walladge
# Distributed under the terms of the GNU General Public License version 3.


import os
from flask import Flask, request, Response, jsonify, session, redirect, url_for, render_template, escape
from functools import wraps
from urllib.parse import parse_qs, quote, unquote
import base64
import json
import bcrypt
import random
import uuid
from pymongo import MongoClient

from notesdb import NotesDB

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


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

def create_user(username, password):
    """ function to create a new user in the db - should also check for errors"""
    # TODO: verify here, or in server part? use flashing (http://flask.pocoo.org/docs/0.10/patterns/flashing/#message-flashing-pattern) to show login/register/etc errors
    if not username or not password:
        return False

    users_db = app.config.get('database')['users']
    if len(username) < 30 and len(username) > 0 and not users_db.find_one({'username': username}):
        users_db.insert({'username': username, 'hashed': bcrypt.hashpw(password.encode(), bcrypt.gensalt())})
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
@crossdomain(origin='*')
@requires_auth
def get_note(user, note_id, version=None):
    note = user.get_note(note_id, version)
    if note is None:
        return Response("Cannot get: note not found",404)

    return jsonify(**note)
    #return "data endpoint - get note id:%s, version:%s" % (note_id, str(version))


@app.route("/api2/data/<note_id>", methods=['POST'])
@crossdomain(origin='*')
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
@crossdomain(origin='*')
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
@crossdomain(origin='*')
@requires_auth
def delete_note(user, note_id):
    status, data = user.delete_note(note_id)

    if status == 200:
        return ""
    else:
        return Response(data, status)
    
    #return "data endpoint - delete note id:%s" % (note_id)


@app.route("/api2/index")
@crossdomain(origin='*')
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
@crossdomain(origin='*')
def login():

    # email and password given in querystring format in post data urlencoded then base64 encoded
    data = request.get_data()
    credentials = parse_qs(unquote(base64.decodestring(data).decode(encoding='UTF-8')))
    print(credentials)

    if "email" in credentials and "password" in credentials:
        email = credentials["email"][0]
        password = credentials["password"][0]
    else:
        return Response("invalid or missing credentials", 401)
    
    if check_auth(email, password):
        return get_token(email) # note this function not secured due to check_auth protecting it

    return Response("invalid credentials", 401)

@app.route('/')
def web_index():
    if 'username' in session:
        # user is logged in, TODO render template for index page
        return 'Logged in as %s' % escape(session['username'])
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def web_login():
    if request.method == 'POST':
        username = request.form['username']
        if not check_auth(username, request.form['password']):
            # TODO: invalid credentials, return login page with message
            return "fail"

        # ok, we're authed, lets set username session
        session['username'] = request.form['username']
        return redirect(url_for('web_index'))

    # TODO: render template for login page
    return '''
        Login
        <form action="" method="post">
            <p>Username <input type=text name=username>
            <p>Password <input type=password name=password>
            <p><input type=submit value=Login>
        </form>
    '''

@app.route('/logout')
def web_logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('web_index'))

@app.route('/register', methods=['GET', 'POST'])
def web_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if create_user(username, password):
            return redirect('/login')
        return '''
            Register again (failed)
            <form action="" method="post">
                <p>Username <input type=text name=username>
                <p>Password <input type=password name=password>
                <p><input type=submit value=Login>
            </form>
            '''
    return '''
        Register
        <form action="" method="post">
            <p>Username <input type=text name=username>
            <p>Password <input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        '''


if __name__ == '__main__':
    app.config.from_object('config')

    if os.environ.get('FLASK_SIMPLENOTE_SRV'):
        app.config.from_envvar('FLASK_SIMPLENOTE_SRV')

    mongo_client = MongoClient(app.config.get('MONGO_HOST'), app.config.get('MONGO_PORT'))
    app.config['mongo_client'] = mongo_client
    app.config['database'] = mongo_client[app.config.get('DATABASE_ROOT_NAME')]
    app.config['users_cache'] = {}
    app.secret_key = app.config.get('SECRET_KEY')

    app.run(
            host=app.config.get('SERVER_BIND'),
            port=app.config.get('SERVER_PORT'),
           # ssl_context = ... better to run this under another web server (eg. nginx or apache) instead of this dev server
            debug = True
            )
