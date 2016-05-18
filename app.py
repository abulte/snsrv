#! /usr/bin/python

# Copyright (c) 2015-2015 Samuel Walladge
# Distributed under the terms of the GNU General Public License version 3.

import os
import re
import json
import base64
import bcrypt
import sqlite3
from functools import wraps
from urllib.parse import parse_qs, unquote

from flask import (
    Flask,
    request,
    Response,
    jsonify,
    session,
    redirect,
    url_for,
    render_template,
    flash,
    g,
    make_response,
    current_app
)

from flask.ext.cors import CORS

import db_frontend

# re to check if string is positive integer (no + prefix allowed)
RE_INT = re.compile(r'\d+')
# re to check if string is positive float (no + prefix allowed)
RE_FLOAT = re.compile(r'\d+(\.\d+|)')

app = Flask(__name__)
CORS(app)

app.config.from_object('config')

if os.environ.get('FLASK_SIMPLENOTE_SRV'):
    app.config.from_envvar('FLASK_SIMPLENOTE_SRV')

DB_TYPE = app.config.get('DB_TYPE')
DB_OPTIONS = app.config.get('DB_OPTIONS')

backend = __import__(DB_TYPE).Database(DB_OPTIONS)
backend.first_run()

db = db_frontend.Database(backend)
app.config['database'] = db

app.secret_key = app.config.get('SECRET_KEY')


def check_auth(username, password):
    """This function is called to check if a username /
       password combination is valid.
       Returns True if valid, False otherwise
    """
    # TODO: maybe this should be done in db_frontend?

    user = app.config['database'].get_user(username)
    if not user:
        return False  # username doesn't exist

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

    status = app.config['database'].create_user(username, bcrypt.hashpw(password.encode(), bcrypt.gensalt()))
    return ("", status)


def requires_auth(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get("auth", None)
        username = request.args.get("email", None)

        # check for existance
        if not username or not token:
            return Response("missing credentials", 401)

        if app.config['database'].check_token(username, token):
            return func(username, *args, **kwargs)

        return Response("invalid credentials", 401)

    return decorated


# TODO: return json error data instead of string over https

# TODO: complete apidoc comments
"""
@apiDefine NoteData

@apiSuccess {String} key the note's unique key
@apiSuccess {Integer} deleted trash status of the note
@apiSuccess {Float}   modifydate time in seconds since epoch
@apiSuccess {Float}   createdate time in seconds since epoch
@apiSuccess {Array}   tags array of tags on the note
@apiSuccess {String}  content the text content of the note
@apiSuccess {Array}   systemtags array of system tags (unread status, pinned, etc.)
@apiSuccess {Integer} syncnum number used for resolving conflicts
@apiSuccess {String} sharekey TODO
@apiSuccess {String} publishkey TODO
@apiSuccess {Integer} version note version
@apiSuccess {Integer} minversion minimum note version available
"""

"""
@api {get} /api2/data/:notekey Get a note by key
@apiName GetNote
@apiGroup Note
@apiPermission User

@apiParam {String} notekey unique note key

@apiUse NoteData
"""

"""
@api {get} /api2/data/:notekey/:version Get a note by key at specified version
@apiName GetNoteVersion
@apiGroup Note
@apiPermission User

@apiParam {String} notekey unique note key
@apiParam {Integer} version version number

@apiSuccess {String} key the note's unique key
@apiSuccess {Float}   versiondate time in seconds since epoch when version created
@apiSuccess {String}  content the text content of the note
@apiSuccess {Integer} version note version
"""
@app.route("/api2/data/<note_id>")
@app.route("/api2/data/<note_id>/<int:version>")
@requires_auth
def get_note(username, note_id, version=None):
    db = app.config.get('database')
    note = db.get_note(username, note_id, version)
    if note is None:
        return Response("Cannot get: note not found", 404)

    return jsonify(**note)


@app.route("/api2/data/<note_id>", methods=['POST'])
@requires_auth
def update_note(username, note_id):
    data = request.get_data().decode(encoding='utf-8')
    # not sure if need this
    if data.lstrip().startswith('%7B'):  # someone urlencoded the post data :(
        data = unquote(data)

    try:
        data = json.loads(data)
    except ValueError:
        return Response("invalid json data", 400)

    data, status = app.config['database'].update_note(username, note_id, data)

    if status == 200:
        return jsonify(**data)
    return Response(data, status)


@app.route("/api2/data", methods=['POST'])
@requires_auth
def create_note(username):
    data = request.get_data().decode(encoding='utf-8')
    if not data:
        return Response("no note data", 400)
    # TODO: check this behaviour
    if data.lstrip().startswith('%7B'):  # someone urlencoded the post data :(
        data = unquote(data)

    try:
        data = json.loads(data)
    except ValueError:
        return Response("invalid json data", 400)

    data, ok = app.config['database'].create_note(username, data)

    if ok:
        return jsonify(**data)
    return Response(data, 400)


@app.route("/api2/data/<notekey>", methods=['DELETE'])
@requires_auth
def delete_note(user, notekey):
    message, status = app.config['database'].delete_note(user, notekey)

    return Response(message, status)


@app.route("/api2/index")
@requires_auth
def get_notes_list(username):

    # all info in the querystring
    length = request.args.get("length", "100")
    since = request.args.get("since", "0")
    mark = request.args.get("mark", None)

    if RE_INT.match(length):
        length = int(length)
    else:
        return Response("invalid length parameter", 400)

    if RE_FLOAT.match(since):
        since = float(since)
    else:
        return Response("invalid since parameter", 400)

    # note: mark can be anything - leave it to the database to work it out

    data, status = app.config['database'].notes_index(username, length, since, mark)

    if status == 200:
        return jsonify(**data)
    else:
        return Response(data, status)

# TODO: tags api


@app.route('/api/login', methods=['POST'])
def login():

    # email and password given in querystring format in post data urlencoded then base64 encoded
    data = request.get_data()
    credentials = parse_qs(base64.decodebytes(data).decode(encoding='UTF-8'))

    if "email" in credentials and "password" in credentials:
        email = unquote(credentials["email"][0])
        password = unquote(credentials["password"][0])
    else:
        return Response("invalid or missing credentials", 401)

    if check_auth(email, password):
        return app.config['database'].get_token(email)

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
        message, status = create_user(username, password)
        if status:
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


# i know the built-in row factory is faster, but I want a dictionary.
def dict_factory(cursor, row):
    mydict = {}
    for idx, col in enumerate(cursor.description):
        mydict[col[0]] = row[idx]
    return mydict


# needed for setup of connections for sqlite database (otherwise get threading issues)
@app.before_request
def before_request():
    if app.config.get('DB_TYPE') == 'sqlite_db':
        g.con = sqlite3.connect(app.config.get('DB_OPTIONS').get('FILE'))
        g.con.row_factory = dict_factory  # so returns dictionary of stuff, rather than tuples
        g.cur = g.con.cursor()


@app.teardown_request
def teardown_request(exception):
    if app.config.get('DB_TYPE') == 'sqlite_db':
        if hasattr(g, 'db'):
            g.con.close()

if __name__ == '__main__':
    app.run(
        host=app.config.get('SERVER_BIND'),
        port=app.config.get('SERVER_PORT'),
        # ssl_context = ... better to run this under another web server
        #   (eg. nginx or apache) instead of this dev server
        debug=True
    )
