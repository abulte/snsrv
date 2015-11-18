#! /usr/bin/python

from flask import Flask, request
#from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

from functools import wraps
from flask import request, Response

users = {}

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    #TODO: proper authentication method and token generation
    if username == 'admin' and password == 'secret':
        users["admin"] = "abcdef" # the token
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
        print("auth attempt:", email, token)
        if email in users:
            if users[email] == token:
                return f(*args, **kwargs)
        return authenticate()
    return decorated

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route("/api/data/<note_id>/<int:version>")
@app.route("/api/data/<note_id>", methods=['GET','POST'])
@requires_auth
def get_note(note_id, version=None):
    if request.method == 'POST':
        #TODO: update the specified note with new content
        pass 
    else:
        #TODO: get and return the specified note
        pass
    return "data get endpoint"


@app.route("/api/data", methods=['POST'])
@requires_auth
def create_note():
    #TODO: create new note
    return "data add endpoint"


@app.route("/api/index")
@requires_auth
def get_notes_list():
    #TODO: return list of notes
    # all info in the querystring
    return "data index endpoint"


@app.route('/api/login')
def get_auth_token():
    email = request.args.get("email","")
    password = request.args.get("password","")

    #TODO: proper authentication procedure
    if check_auth(email, password):
        return users[email] # the token

    return authenticate()


if __name__ == '__main__':
    app.run(
            #host='0.0.0.0',
            debug=True
            )



