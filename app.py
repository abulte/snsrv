#! /usr/bin/python

from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route("/data/<note_id>/<int:version>")
@app.route("/data/<note_id>", methods=['GET','POST'])
def get_note(note_id, version=None):
    if request.method == 'POST':
        pass # update note
    else:
        pass # get note
    return "hey!"


@app.route("/data", methods=['POST'])
def create_note():
    if request.method == 'POST':
        pass # update note
    else:
        pass # get note
    return "hey post!"


@app.route("/index")
def get_notes_list():
    # return list of notes
    # all info in the querystring
    return "hey!!"






if __name__ == '__main__':
    app.run(
            #debug=True,
            #host='0.0.0.0'
            )
