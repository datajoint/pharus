"""Exposed REST API."""
from os import environ
from .interface import DJConnector
from . import __version__ as version
from typing import Callable

# Crypto libaries
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

from flask import Flask, request
import jwt
from json import loads
from base64 import b64decode

app = Flask(__name__)
# Check if PRIVATE_KEY and PUBIC_KEY is set, if not generate them.
# NOTE: For web deployment, please set the these enviorment variable to be the same between
# the instance
if environ.get('PHARUS_PRIVATE_KEY') is None or environ.get('PHARUS_PUBLIC_KEY') is None:
    key = rsa.generate_private_key(backend=crypto_default_backend(),
                                   public_exponent=65537,
                                   key_size=2048)
    environ['PHARUS_PRIVATE_KEY'] = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption()).decode()
    environ['PHARUS_PUBLIC_KEY'] = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    ).decode()


def protected_route(function: Callable):
    """
    Protected route function decorator which authenticates requests
    :param function: Function to decorate, typically routes
    :type function: :class:`typing.Callable`
    :return: Function output if jwt authecation is successful, otherwise return error message
    :rtype: class:`typing.Callable`
    """
    def wrapper():
        try:
            jwt_payload = jwt.decode(request.headers.get('Authorization').split()[1],
                                     environ['PHARUS_PUBLIC_KEY'], algorithms='RS256')
            return function(jwt_payload)
        except Exception as e:
            return str(e), 401

    wrapper.__name__ = function.__name__
    return wrapper


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/version")
def api_version():
    """
    Route to check if the server is alive or not
    :return: API version
    :rtype: str
    """
    return version


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/login", methods=['POST'])
def login():
    """
    Login route which uses DataJoint database server login. Expects:
        (html:POST:body): json with keys
            {databaseAddress: string, username: string, password: string}
    :return: Function output if jwt authecation is successful, otherwise return error message
    :rtype: dict
    """
    # Check if request.json has the correct fields
    if not request.json.keys() >= {'databaseAddress', 'username', 'password'}:
        return dict(error='Invalid json body')

    # Try to login in with the database connection info, if true then create jwt key
    try:
        DJConnector.attempt_login(request.json['databaseAddress'],
                                  request.json['username'],
                                  request.json['password'])
        # Generate JWT key and send it back
        encoded_jwt = jwt.encode(request.json, environ['PHARUS_PRIVATE_KEY'],
                                 algorithm='RS256')
        return dict(jwt=encoded_jwt)
    except Exception as e:
        return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/list_schemas", methods=['GET'])
@protected_route
def list_schemas(jwt_payload: dict):
    """
    API route for fetching schema. Expects:
        (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
    :param jwt_payload: Dictionary containing databaseAddress, username and password
        strings.
    :type jwt_payload: dict
    :return: If sucessfuly sends back a list of schemas names otherwise returns error
    :rtype: dict
    """
    # Get all the schemas
    try:
        schemas_name = DJConnector.list_schemas(jwt_payload)
        return dict(schemaNames=schemas_name)
    except Exception as e:
        return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/list_tables", methods=['POST'])
@protected_route
def list_tables(jwt_payload: dict):
    """
    API route for listing all tables under a given schema name. Expects:
        (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
        (html:POST:JSON): {"schemaName": <schema_name>}
    :param jwt_payload: Dictionary containing databaseAddress, username and password
        strings.
    :type jwt_payload: dict
    :return: If successful then sends back a list of tables names otherwise returns error
    :rtype: dict
    """
    try:
        tables_dict_list = DJConnector.list_tables(jwt_payload, request.json["schemaName"])
        return dict(tableTypeAndNames=tables_dict_list)
    except Exception as e:
        return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/fetch_tuples", methods=['POST'])
@protected_route
def fetch_tuples(jwt_payload: dict):
    """
    Route to fetch all records for a given table. Expects:
        (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
        (html:query_params): {"limit": <limit>, "page": <page>, "order": <order>,
                              "restriction": <Base64 encoded restriction as JSONArray>}
        (html:POST:JSON): {"schemaName": <schema_name>, "tableName": <table_name>}
            NOTE: Table name must be in CamalCase
    :param jwt_payload: Dictionary containing databaseAddress, username and password
        strings.
    :type jwt_payload: dict
    :return: If successful then sends back records as list otherwise returns error
    :rtype: dict
    """
    try:
        table_tuples, total_count = DJConnector.fetch_tuples(
            jwt_payload=jwt_payload,
            schema_name=request.json["schemaName"],
            table_name=request.json["tableName"],
            **{k: (int(v) if k in ('limit', 'page')
                   else (v.split(',') if k == 'order' else loads(
                       b64decode(v.encode('utf-8')).decode('utf-8'))))
               for k, v in request.args.items()},
            )
        return dict(tuples=table_tuples, total_count=total_count)
    except Exception as e:
        return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/get_table_definition", methods=['POST'])
@protected_route
def get_table_definition(jwt_payload: dict):
    """
    Route to get table definition. Expects:
        (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
        (html:POST:JSON): {"schemaName": <schema_name>, "tableName": <table_name>}
            NOTE: Table name must be in CamalCase
    :param jwt_payload: Dictionary containing databaseAddress, username and password
        strings.
    :type jwt_payload: dict
    :return: If successful then sends back definition for table otherwise returns error
    :rtype: str
    """
    try:
        table_definition = DJConnector.get_table_definition(jwt_payload,
                                                            request.json["schemaName"],
                                                            request.json["tableName"])
        return table_definition
    except Exception as e:
        return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/get_table_attributes", methods=['POST'])
@protected_route
def get_table_attributes(jwt_payload: dict):
    """
    Route to get table attibutes. Expects:
        (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
        (html:POST:JSON): {"schemaName": <schema_name>, "tableName": <table_name>}
            NOTE: Table name must be in CamalCase
    :param jwt_payload: Dictionary containing databaseAddress, username and password
        strings.
    :type jwt_payload: dict
    :return: If successful then sends back dict of table attributes otherwise returns error
    :rtype: dict
    """
    try:
        return DJConnector.get_table_attributes(jwt_payload,
                                                request.json["schemaName"],
                                                request.json["tableName"])
    except Exception as e:
        return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/insert_tuple", methods=['POST'])
@protected_route
def insert_tuple(jwt_payload: dict):
    """
    Route to insert record. Expects:
        (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
        (html:POST:JSON): {"schemaName": <schema_name>, "tableName": <table_name>,
                           "tuple": <tuple_to_insert>}
            NOTE: Table name must be in CamalCase
    :param jwt_payload: Dictionary containing databaseAddress, username and password
        strings.
    :type jwt_payload: dict
    :return: If successful then returns "Insert Successful" otherwise returns error
    :rtype: dict
    """
    try:
        # Attempt to insert
        DJConnector.insert_tuple(jwt_payload,
                                 request.json["schemaName"],
                                 request.json["tableName"],
                                 request.json["tuple"])
        return "Insert Successful"
    except Exception as e:
        return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/record/dependency", methods=['GET'])
@protected_route
def record_dependency(jwt_payload: dict) -> dict:
    """
    Route to insert record. Expects:
        (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
        (html:query_params): {"schemaName": <schema_name>, "tableName": <table_name>,
                           "restriction": <b64 JSON restriction>}
            NOTE: Table name must be in CamalCase
    :param jwt_payload: Dictionary containing databaseAddress, username and password
        strings.
    :type jwt_payload: dict
    :return: If sucessfuly sends back a list of dependencies otherwise returns error
    :rtype: dict
    """
    # Get dependencies
    try:
        dependencies = DJConnector.record_dependency(
            jwt_payload, request.args.get('schemaName'), request.args.get('tableName'),
            loads(b64decode(request.args.get('restriction').encode('utf-8')).decode('utf-8')))
        return dict(dependencies=dependencies)
    except Exception as e:
        return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/update_tuple", methods=['POST'])
@protected_route
def update_tuple(jwt_payload: dict):
    """
    Route to update record. Expects:
        (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
        (html:POST:JSON): {"schemaName": <schema_name>, "tableName": <table_name>,
                           "tuple": <tuple_to_insert>}
            NOTE: Table name must be in CamalCase
    :param jwt_payload: Dictionary containing databaseAddress, username and password
        strings.
    :type jwt_payload: dict
    :return: If successful then returns "Update Successful" otherwise returns error
    :rtype: dict
    """
    try:
        # Attempt to insert
        DJConnector.update_tuple(jwt_payload,
                                 request.json["schemaName"],
                                 request.json["tableName"],
                                 request.json["tuple"])
        return "Update Successful"
    except Exception as e:
        return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/delete_tuple", methods=['POST'])
@protected_route
def delete_tuple(jwt_payload: dict):
    """
    Route to delete a specific record. Expects:
        (html:GET:Authorization): Must include in format of: bearer <JWT-Token>
        (html:POST:JSON): {"schemaName": <schema_name>, "tableName": <table_name>,
                           "restrictionTuple": <tuple_to_restrict_table_by>}
            NOTE: Table name must be in CamalCase
    :param jwt_payload: Dictionary containing databaseAddress, username and password
        strings.
    :type jwt_payload: dict
    :return: If successful then returns "Delete Successful" otherwise returns error
    :rtype: dict
    """
    try:
        # Attempt to delete tuple
        DJConnector.delete_tuple(jwt_payload,
                                 request.json["schemaName"],
                                 request.json["tableName"],
                                 request.json["restrictionTuple"])
        return "Delete Sucessful"
    except Exception as e:
        return str(e), 500


def run():
    """
    Starts API server.
    """
    app.run(host='0.0.0.0', port=environ.get('PHARUS_PORT', 5000))


if __name__ == '__main__':
    run()
