#! /usr/bin/bash

# test login
printf "email=admin&password=secret" | base64 -w 0 | http post http://localhost:5000/api/login

# test create new note
printf '{"content": "haha"}' | http post http://localhost:5000/api/data email==admin

# test retrieve a note
http get localhost:5000/api/data/1b4877dc34e611e585ce399adaa77b5c/8 email==admin
