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
            return str(e), 401

    wrapper.__name__ = function.__name__
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
API route for fetching schema

Parameters:
    header: (html:GET:Authorization): Must include in format of: bearer <JWT-Token>

Returns:
    dict(schemaNames=<schemas>): If sucessfuly send back a list of schemas names
    or
    dict(error=<error_message>): With error message of why it failed
"""
@app.route('/api/list_schemas', methods=['GET'])
@protected_route
def list_schemas(jwt_payload):
    # Get all the schemas
    try:
        schemas_name = DJConnector.list_schemas(jwt_payload)
        return dict(schemaNames=schemas_name)
    except Exception as e:
        return str(e), 500

"""
API route for listing all tables under a given schema name

Parameters:
    header: (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
    body: (html:POST:JSON): {"schemaName": <schema_name>}

Returns:
    dict(
        manualTables=[<tables_names>], 
        lookupTables=[<tables_names>], 
        computeTables=[<tables_name>], 
        partTables=[<parent_table.part_table_name>]
        ): If successful then send back a list of tables names
    or
    dict(error=<error_message>): With error message of why it failed
"""
@app.route('/api/list_tables', methods=['POST'])
@protected_route
def list_tables(jwt_payload):
    try:
        tables_dict_list = DJConnector.list_tables(jwt_payload, request.json["schemaName"])
        return dict(tableTypeAndNames = tables_dict_list)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)