import os
import sys
from DJConnector import DJConnector

from flask import Flask, request
import jwt
app = Flask(__name__)

@app.route('/api')
def hello_world():
    return 'Hello, World!'

@app.route('/api/login', methods=['POST'])
def login():
    # Check if request.json has the correct fields
    if not request.json.keys() >= {'databaseAddress', 'username', 'password'}:
        return dict(error='Invalid json body')

    # Try to login in with the database connection info, if true then create jwt key
    if DJConnector.attempt_login(request.json['databaseAddress'], request.json['username'], request.json['password']):
        # Generate JWT key and send it back
        encoded_jwt = jwt.encode(request.json, os.environ['PRIVATE_KEY'].encode(), algorithm='RS256')
        return dict(jwt=encoded_jwt.decode())
    else:
        return dict(error='Invalid Credentials')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)