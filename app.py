#! /usr/bin/python

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

    users_db = main_database['users']

    user = users_db.find_one({'username': username})
    if not user:
        return False # username doesn't exist

    print("user %s ok" % (username))
    print(user)

    # check if equal to password in database
    if bcrypt.hashpw(password.encode(), user['hashed']) == user['hashed']:
        return True

    return False


def get_token(username):
    """ returns a valid token for the given user (generates new one if needed)
        currently doesn't validate user - expected to be protected by check_auth function
    """

    db = main_database['users']
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
        email = request.args.get("email",None)

        # check for existance
        if email is None or token is None:
            return Response("invalid or missing credentials", 401)

        # check for user existance
        user = main_database['users'].find_one({'username': email})
        if not user:
            return Response("invalid or missing credentials", 401)

        # check token valid. TODO: token expire time
        if user['token'] == token and user.get('tokenisvalid', False):
            return f(NotesDB(main_database['notes'][email]), *args, **kwargs)

        return Response("invalid credentials", 401)

    return decorated


app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route("/api2/data/<note_id>/<int:version>")
@app.route("/api2/data/<note_id>")
@requires_auth
def get_note(user, note_id, version=None):
    #print(users[user]['notesdb'])
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
    #data = request.get_json(force=True)
    #print(data)
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

    # email and password given in querystring format in post data base64 encoded
    data = request.get_data()
    credentials = parse_qs(base64.decodestring(data).decode(encoding='UTF-8'))

    print(credentials)
    if "email" in credentials and "password" in credentials:
        email = credentials["email"][0]
        password = credentials["password"][0]
    else:
        return Response("invalid or missing credentials", 401)
    
    if check_auth(email, password):
        return get_token(email) # note this function not secured due to check_auth protecting it

    return Response("invalid credentials", 401)



mongo_client = MongoClient()
main_database = mongo_client['simplenote1']

class User():
    def __init__(self, name):
        self.name = name


if __name__ == '__main__':
    app.run(
            #host='0.0.0.0',
            #port=80,
            debug=True
            )



