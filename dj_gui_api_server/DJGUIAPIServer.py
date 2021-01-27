import os
import sys
from DJConnector import DJConnector

# Crypto libaries
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

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
    string: With error message of why it failed, 500 error
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
    string: With error message of why it failed, 500 error
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
        manual_tables=[<tables_names>], 
        lookup_tables=[<tables_names>], 
        compute_tables=[<tables_name>],
        imported_tables=[<imported_tables>],
        part_tables=[<parent_table.part_table_name>]
        ): If successful then send back a list of tables names
    or
    string: With error message of why it failed, 500 error
"""
@app.route('/api/list_tables', methods=['POST'])
@protected_route
def list_tables(jwt_payload):
    try:
        tables_dict_list = DJConnector.list_tables(jwt_payload, request.json["schemaName"])
        return dict(tableTypeAndNames = tables_dict_list)
    except Exception as e:
        return str(e), 500

"""
Route to fetch all tuples for a given table

Parameters:
    header: (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
    body: (html:POST:JSON): {"schemaName": <schema_name>, "tableName": <table_name>} (NOTE: Table name must be in CamalCase)

Returns:
    dict(tuples=tuples): Tuples will be represented as a list
    or
    string: With error message of why it failed, 500 error
"""
@app.route('/api/fetch_tuples', methods=['POST'])
@protected_route
def fetch_tuples(jwt_payload):
    try:
        table_tuples = DJConnector.fetch_tuples(jwt_payload, request.json["schemaName"], request.json["tableName"])
        return dict(tuples = table_tuples)
    except Exception as e:
        return str(e), 500

"""
Route to get table definition

Parameters:
    header: (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
    body: (html:POST:JSON): {"schemaName": <schema_name>, "tableName": <table_name>} (NOTE: Table name must be in CamalCase)

Returns:
    dict(tuples=[tuples_as_dicts])
    or
    string: With error message of why it failed, 500 error
"""
@app.route('/api/get_table_definition', methods=['POST'])
@protected_route
def get_table_definition(jwt_payload):
    try:
        table_definition = DJConnector.get_table_definition(jwt_payload, request.json["schemaName"], request.json["tableName"])
        return dict(definition = table_definition)
    except Exception as e:
        return str(e), 500

"""
Route to get table attibutes

Parameters:
    header: (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
    body: (html:POST:JSON): {"schemaName": <schema_name>, "tableName": <table_name>} (NOTE: Table name must be in CamalCase)

Returns:
    dict(primary_attributes=[tuple(attribute_name, type, nullable, default, autoincrement)], secondary_attributes=[tuple(attribute_name, type, nullable, default, autoincrement)])
    or
    string: With error message of why it failed, 500 error
"""
@app.route('/api/get_table_attributes', methods=['POST'])
@protected_route
def get_table_attributes(jwt_payload):
    try:
        return DJConnector.get_table_attributes(jwt_payload, request.json["schemaName"], request.json["tableName"])
    except Exception as e:
        return str(e), 500

"""
Route to insert tuple

Parameter:
    Parameters:
    header: (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
    body: (html:POST:JSON): {"schemaName": <schema_name>, "tableName": <table_name>, "tuple": <tuple_to_insert>} (NOTE: Table name must be in CamalCase)

Returns:
    string: "Insert Successful" if the tuple was insert sucessfully
    or
    string: With error message of why it failed, 500 error
"""
@app.route('/api/insert_tuple', methods=['POST'])
@protected_route
def insert_tuple(jwt_payload):
    try:
        # Attempt to insert
        DJConnector.insert_tuple(jwt_payload, request.json["schemaName"], request.json["tableName"], request.json["tuple"])
        return "Insert Successful"
    except Exception as e:
        return str(e), 500

"""
Route to delete a specific tuple

Parameter:
    Parameters:
    header: (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
    body: (html:POST:JSON): {"schemaName": <schema_name>, "tableName": <table_name>, "restrictionTuple": <tuple_to_restrict_table_by>} (NOTE: Table name must be in CamalCase)

Returns:
    string: "Delete Successful" if the tuple was deleted sucessfully
    or
    string: With error message of why it failed, 500 error
"""
@app.route('/api/delete_tuple', methods=['POST'])
@protected_route
def delete_tuple(jwt_payload):
    try:
        # Attempt to delete tuple
        DJConnector.delete_tuple(jwt_payload, request.json["schemaName"], request.json["tableName"], request.json["restrictionTuple"])
        return "Delete Sucessful"
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    # Check if PRIVATE_KEY and PUBIC_KEY is set, if not generate them.
    # NOTE: For web deployment, please set the these enviorment variable to be the same between the instance
    if os.environ.get('PRIVATE_KEY') == None or os.environ.get('PUBLIC_KEY') == None:
        key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048
        )
        os.environ['PRIVATE_KEY'] = key.private_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PrivateFormat.PKCS8,
            crypto_serialization.NoEncryption()).decode()
        os.environ['PUBLIC_KEY'] = key.public_key().public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH
        ).decode()

    app.run(host='0.0.0.0', port=5000)