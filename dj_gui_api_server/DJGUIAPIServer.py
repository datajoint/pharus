import os
import sys
from DJConnector import DJConnector

from flask import Flask, request
import jwt
app = Flask(__name__)

"""
Protected route function decrator

Parameters:
    function: function to decreate, typically routes

Returns:
    Return function output if jwt authecation is successful, otherwise return error message
"""
def protected_route(function):
    def wrapper():
        try:
            jwt_payload = jwt.decode(request.headers.get('Authorization')[7:], os.environ['PUBLIC_KEY'], algorithm='RS256')
            return function(jwt_payload)
        except Exception as e:
            return dict(error=str(e))
    return wrapper

"""
Route to check if the server is alive or not
"""
@app.route('/api')
def hello_world():
    return 'Hello, World!'

"""
# Login route which uses datajoint login

Parameters:
    (html:POST:body): json with keys {databaseAddress: string, username: string, password: string}

Returns:
    dict(jwt=<JWT_TOKEN>): If sucessfully authenticated against the database
    or
    dict(error=<error_message>): With error message of why it failed
"""
@app.route('/api/login', methods=['POST'])
def login():
    # Check if request.json has the correct fields
    if not request.json.keys() >= {'databaseAddress', 'username', 'password'}:
        return dict(error='Invalid json body')

    # Try to login in with the database connection info, if true then create jwt key
    attempt_connection_result = DJConnector.attempt_login(request.json['databaseAddress'], request.json['username'], request.json['password'])
    if attempt_connection_result['result']:
        # Generate JWT key and send it back
        encoded_jwt = jwt.encode(request.json, os.environ['PRIVATE_KEY'], algorithm='RS256')
        return dict(jwt=encoded_jwt.decode())
    else:
        return dict(error=str(attempt_connection_result['error']))

"""
# API route for fetching schema

Parameters:
    (html:POST:body): json with keys {}

Returns:
    dict(schemas=<schemas>): If sucessfuly send back a list of schemas names
    or
    dict(error=<error_message>): With error message of why it failed
"""
@app.route('/api/list_schemas', methods=['GET'])
@protected_route
def list_schemas(jwt_payload):
    print(jwt_payload, flush=True)
    # Get all the schemas
    result = DJConnector.list_schemas(jwt_payload['databaseAddress'], jwt_payload['username'], jwt_payload['password'])
    if result['result']:
        return dict(schemas=result['schemas'])
    else:
        return dict(error=result['error'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)