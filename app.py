#! /usr/bin/python

# Copyright (c) 2015 Samuel Walladge
# Distributed under the terms of the GNU General Public License version 3.


import os
from flask import Flask, request, Response, jsonify, \
        session, redirect, url_for, render_template, escape, \
        flash, g
from functools import wraps
from urllib.parse import parse_qs, quote, unquote
import base64
import json
import bcrypt
import random
import uuid
import sqlite3

# TODO: get rid of these
from notesdb import NotesDB
from pymongo import MongoClient


from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

import db_frontend


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
    # TODO: maybe this should be done in db_frontend?

    db = app.config.get('database')

    user = db.get_user(username)
    if not user:
        return False # username doesn't exist

    # check if equal to password in database
    if bcrypt.hashpw(password.encode(), user['hashed']) == user['hashed']:
        return True

    return False

def create_user(username, password):
    """ function to create a new user in the db - should also validate"""
    if not username or not password:
        return ("username and password are required fields!", False)
    if len(password) < 8:
        return ("password must 8 or more characters", False)
    if len(username) < 1 or len(username) > 40:
        return ("username invalid length", False)

    status = db.create_user(username, bcrypt.hashpw(password.encode(), bcrypt.gensalt()))
    return ("", status)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get("auth",None)
        username = request.args.get("email",None)

        # check for existance
        if not username or not token:
            return Response("missing credentials", 401)

        ok = db.check_token(username, token)
        if ok:
            return f(user['id'], *args, **kwargs)

        return Response("invalid credentials", 401)

    return decorated


app = Flask(__name__)


@app.route("/api2/data/<note_id>/<int:version>")
@app.route("/api2/data/<note_id>")
@crossdomain(origin='*')
@requires_auth
def get_note(userid, note_id, version=None):
    db = app.config.get('database')
    note = db.get_note(userid, note_id, version)
    if note is None:
        return Response("Cannot get: note not found",404)

    return jsonify(**note)


@app.route("/api2/data/<note_id>", methods=['POST'])
@crossdomain(origin='*')
@requires_auth
def update_note(userid, note_id):
    data = request.get_data().decode(encoding='utf-8')
    # not sure if need this
    if data.lstrip().startswith('%7B'): # someone urlencoded the post data :(
        data = unquote(data)

    data = json.loads(data)

    status, data = db.update_note(userid, note_id, data)

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
    credentials = parse_qs(base64.decodestring(data).decode(encoding='UTF-8'))

    if "email" in credentials and "password" in credentials:
        email = unquote(credentials["email"][0])
        password = unquote(credentials["password"][0])
    else:
        return Response("invalid or missing credentials", 401)
    
    if check_auth(email, password):
        return db.get_token(email) 

    return Response("invalid credentials", 401)

@app.route('/')
def web_index():
    loggedin = False
    if 'username' in session:
        loggedin = True
    return render_template('index.html', username=session.get('username', None), loggedin=loggedin)

@app.route('/login', methods=['GET', 'POST'])
def web_login():
    if request.method == 'POST':
        username = request.form['username']
        if not check_auth(username, request.form['password']):
            return render_template('login.html', error='Invalid credentials') 

        # ok, we're authed, lets set username session
        session['username'] = request.form['username']
        return redirect(url_for('web_index'))

    if 'username' in session:
        flash("You are logged in!")
        return redirect(url_for('web_index'))
    return render_template('login.html', error=None) 


@app.route('/logout')
def web_logout():
    # remove the username from the session if it's there
    if session.pop('username', None):
        flash("You have been logged out.")
    return redirect(url_for('web_index'))

@app.route('/register', methods=['GET', 'POST'])
def web_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        message, ok = create_user(username, password)
        if ok:
            return redirect('/login')

        return '''
            Try again! {}
            <form action="" method="post">
                <p>Username <input type=text name=username>
                <p>Password <input type=password name=password>
                <p><input type=submit value=Register>
            </form>
            '''.format(message)
    return '''
        Register
        <form action="" method="post">
            <p>Username <input type=text name=username>
            <p>Password <input type=password name=password>
            <p><input type=submit value=Register>
        </form>
        '''
def connect_db():
    return sqlite3.connect('sqlite.db')

@app.before_request
def before_request():
    g.db = connect_db()
    g.db.row_factory = sqlite3.Row # so returns dictionary of stuff, rather than tuples

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

if __name__ == '__main__':
    app.config.from_object('config')

    if os.environ.get('FLASK_SIMPLENOTE_SRV'):
        app.config.from_envvar('FLASK_SIMPLENOTE_SRV')


    db_type = app.config.get('DB_TYPE')
    options = app.config.get('DB_OPTIONS')

    backend = __import__(db_type).Database(options)
    backend.first_run()

    global db
    db = db_frontend.Database(backend)
    app.config['database'] = db

    app.secret_key = app.config.get('SECRET_KEY')

    app.run(
            host=app.config.get('SERVER_BIND'),
            port=app.config.get('SERVER_PORT'),
           # ssl_context = ... better to run this under another web server (eg. nginx or apache) instead of this dev server
            debug = True
            )
