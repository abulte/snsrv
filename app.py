#! /usr/bin/python

from flask import Flask, request, Response, jsonify
#from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

from functools import wraps
from urllib.parse import parse_qs

import base64
from pymongo import MongoClient

from notesdb import NotesDB



def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    #TODO: proper authentication method and token generation
    if username == 'admin' and password == 'secret':
        users["admin"] = {  "token":"abcdef", # the token
                            "notesdb": NotesDB(mongo_client["notes"]["admin"]) # this is a database object containing all of 'admin's notes
                         }
        return True
    return False

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get("auth","")
        email = request.args.get("email","")
        print("token auth attempt:", email, token)
        # straight through for debugging
        return f(email, *args, **kwargs)
        if email in users:
            if users[email]['token'] == token:
                return f(email, *args, **kwargs)
        return authenticate()
    return decorated

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route("/api/data/<note_id>/<int:version>")
@app.route("/api/data/<note_id>")
@requires_auth
def get_note(user, note_id, version=None):
    #print(users[user]['notesdb'])
    note = users[user]['notesdb'].get_note(note_id, version)
    if note is None:
        return Response("Cannot get: note not found",404)

    return jsonify(**note)
    #return "data endpoint - get note id:%s, version:%s" % (note_id, str(version))


@app.route("/api/data/<note_id>", methods=['POST'])
@requires_auth
def update_note(user, note_id):
    data = request.get_data()
    data = request.get_json(force=True)
    note = users[user]['notesdb'].update_note(note_id, data)

    if note is None:
        return Response("Cannot update: note not found",404)

    return jsonify(**note)
    #return "data endpoint - update note id:%s" % (note_id)


@app.route("/api/data", methods=['POST'])
@requires_auth
def create_note(user):
    data = request.get_data()
    data = request.get_json(force=True)
    print(data)
    note = users[user]['notesdb'].create_note(data)

    if note is None:
        return Response("Cannot create: unknown error",500)

    return jsonify(**note)


@app.route("/api/data/<note_id>", methods=['DELETE'])
@requires_auth
def delete_note(user, note_id):
    #TODO: delete the note
    status = users[user]['notesdb'].delete_note(note_id)

    if status == 0:
        return ""
    elif status == 1:
     return Response("Error deleting: unknown error",500)
    elif status == 2:
     return Response("Error deleting: note not found",404)
    elif status == 3:
     return Response("Error deleting: must send note to trash before permanent deletion",403)
    
    #return "data endpoint - delete note id:%s" % (note_id)


@app.route("/api/index")
@requires_auth
def get_notes_list(user):
    #TODO: return list of notes
    # all info in the querystring
    return "data index endpoint"


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
        return authenticate()
    
    #TODO: proper authentication procedure
    if check_auth(email, password):
        return users[email]['token'] # the token

    return authenticate()



mongo_client = MongoClient()
users = {}

# debugging only
users["admin"] = {  "token":"abcdef", # the token
                   "notesdb": NotesDB(mongo_client["notes"]["admin"]) # this is a database object containing all of 'admin's notes
                   }

if __name__ == '__main__':
    app.run(
            #host='0.0.0.0',
            #port=80,
            debug=True
            )



