"""Exposed REST API."""
from os import environ
from .interface import DJConnector
from . import __version__ as version
from typing import Callable
from functools import wraps

# Crypto libaries
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

from flask import Flask, request
import jwt
from json import loads
from base64 import b64decode
from datajoint.errors import IntegrityError
from datajoint.table import foreign_key_error_regexp
from datajoint.utils import to_camel_case

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


def protected_route(function: Callable) -> Callable:
    """
    Protected route function decorator which authenticates requests.

    :param function: Function to decorate, typically routes
    :type function: :class:`~typing.Callable`
    :return: Function output if jwt authetication is successful, otherwise return error
        message
    :rtype: :class:`~typing.Callable`
    """
    @wraps(function)
    def wrapper():
        try:
            jwt_payload = jwt.decode(request.headers.get('Authorization').split()[1],
                                     environ['PHARUS_PUBLIC_KEY'], algorithms='RS256')
            return function(jwt_payload)
        except Exception as e:
            return str(e), 401

    wrapper.__name__ = function.__name__
    return wrapper


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/version", methods=['GET'])
def api_version() -> str:
    """
    Handler for ``/version`` route.

    :return: API version
    :rtype: str

    .. http:get:: /version

        Route to check server health returning the API version.

        **Example request**:

        .. sourcecode:: http

            GET /version HTTP/1.1
            Host: fakeservices.datajoint.io

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: text/plain

            0.1.0

        :statuscode 200: No error.
    """
    if request.method == 'GET':
        return version


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/login", methods=['POST'])
def login() -> dict:
    """
    **WARNING**: Currently, this implementation exposes user database credentials as plain
    text in POST body once and stores it within a bearer token as Base64 encoded for
    subsequent requests. That is how the server is able to submit queries on user's behalf.
    Due to this, it is required that remote hosts expose the server only under HTTPS to ensure
    end-to-end encryption. Sending passwords in plain text over HTTPS in POST request body is
    common and utilized by companies such as GitHub (2021) and Chase Bank (2021). On server
    side, there is no caching, logging, or storage of received passwords or tokens and thus
    available only briefly in memory. This means the primary vulnerable point is client side.
    Users should be responsible with their passwords and bearer tokens treating them as
    one-in-the-same. Be aware that if your client system happens to be compromised, a bad
    actor could monitor your outgoing network requests and capture/log your credentials.
    However, in such a terrible scenario, a bad actor would not only collect credentials for
    your DataJoint database but also other sites such as github.com, chase.com, etc. Please be
    responsible and vigilant with credentials and tokens on client side systems. Improvements
    to the above strategy is currently being tracked in
    https://github.com/datajoint/pharus/issues/82.

    Handler for ``/login`` route.

    :return: Function output is encoded jwt if successful, otherwise return error message
    :rtype: dict

    .. http:post:: /login

        Route to get authentication token.

        **Example request**:

        .. sourcecode:: http

            POST /login HTTP/1.1
            Host: fakeservices.datajoint.io
            Accept: application/json

            {
                "databaseAddress": "tutorial-db.datajoint.io",
                "username": "user1",
                "password": "password1"
            }

        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json

            {
                "jwt": "<token>"
            }


        **Example unexpected response**:

        .. sourcecode:: http

            HTTP/1.1 500 Internal Server Error
            Vary: Accept
            Content-Type: text/plain

            400 Bad Request: The browser (or proxy) sent a request that this server could not
                understand.

        :resheader Content-Type: text/plain, application/json
        :statuscode 200: No error.
        :statuscode 500: Unexpected error encountered. Returns the error message as a string.
    """
    if request.method == 'POST':
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


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/schema", methods=['GET'])
@protected_route
def schema(jwt_payload: dict) -> dict:
    """
    Handler for ``/schema`` route.

    :param jwt_payload: Dictionary containing databaseAddress, username, and password strings.
    :type jwt_payload: dict
    :return: If successful then sends back a list of schemas names otherwise returns error.
    :rtype: dict

    .. http:get:: /schema

        Route to get list of schemas.

        **Example request**:

        .. sourcecode:: http

            GET /schema HTTP/1.1
            Host: fakeservices.datajoint.io

        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json

            {
                "schemaNames": [
                    "alpha_company"
                ]
            }


        **Example unexpected response**:

        .. sourcecode:: http

            HTTP/1.1 500 Internal Server Error
            Vary: Accept
            Content-Type: text/plain

            400 Bad Request: The browser (or proxy) sent a request that this server could not
                understand.

        :reqheader Authorization: Bearer <OAuth2_token>
        :resheader Content-Type: text/plain, application/json
        :statuscode 200: No error.
        :statuscode 500: Unexpected error encountered. Returns the error message as a string.
    """
    if request.method == 'GET':
        # Get all the schemas
        try:
            schemas_name = DJConnector.list_schemas(jwt_payload)
            return dict(schemaNames=schemas_name)
        except Exception as e:
            return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/table", methods=['GET'])
@protected_route
def table(jwt_payload: dict) -> dict:
    """
    Handler for ``/list_tables`` route.

    :param jwt_payload: Dictionary containing databaseAddress, username, and password strings.
    :type jwt_payload: dict
    :return: If successful then sends back a list of tables names otherwise returns error.
    :rtype: dict

    .. http:post:: /list_tables

        Route to get tables within a schema.

        **Example request**:

        .. sourcecode:: http

            POST /list_tables HTTP/1.1
            Host: fakeservices.datajoint.io
            Accept: application/json

            {
                "schemaName": "alpha_company"
            }

        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json

            {
                "tableTypeAndNames": {
                    "computed_tables": [],
                    "imported_tables": [],
                    "lookup_tables": [
                        "Employee"
                    ],
                    "manual_tables": [
                        "Computer"
                    ],
                    "part_tables": []
                }
            }


        **Example unexpected response**:

        .. sourcecode:: http

            HTTP/1.1 500 Internal Server Error
            Vary: Accept
            Content-Type: text/plain

            400 Bad Request: The browser (or proxy) sent a request that this server could not
                understand.

        :reqheader Authorization: Bearer <OAuth2_token>
        :resheader Content-Type: text/plain, application/json
        :statuscode 200: No error.
        :statuscode 500: Unexpected error encountered. Returns the error message as a string.
    """
    if request.method == 'GET':
        try:
            tables_dict_list = DJConnector.list_tables(jwt_payload,
                                                       request.args["schemaName"])
            return dict(tableTypeAndNames=tables_dict_list)
        except Exception as e:
            return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/record", methods=['GET'])
@protected_route
def get_record(jwt_payload: dict) -> dict:
    ("""
    Handler for ``/fetch_tuple`` route.

    :param jwt_payload: Dictionary containing databaseAddress, username, and password strings.
    :type jwt_payload: dict
    :return: If successful then sends back dict with records and total count from query
        otherwise returns error.
    :rtype: dict

    .. http:post:: /fetch_tuple

        Route to fetch records.

        **Example request**:

        .. sourcecode:: http

            POST /fetch_tuples?limit=2&page=1&order=computer_id%20DESC&"""
     "restriction=W3siYXR0cmlidXRlTmFtZSI6ICJjb21wdXRlcl9tZW1vcnkiLCAib3BlcmF0aW9uIjogIj49Iiw"
     "gInZhbHVlIjogMzJ9XQo="
     """ HTTP/1.1
            Host: fakeservices.datajoint.io
            Accept: application/json

            {
                "schemaName": "alpha_company",
                "tableName": "Computer"
            }

        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json

            {
                "total_count": 4,
                "tuples": [
                    [
                        "eee3491a-86d5-4af7-a013-89bde75528bd",
                        "ABCDEFJHE",
                        "Dell",
                        1611705600,
                        2.2,
                        32,
                        11.5,
                        "1100.93",
                        5,
                        1614265209,
                        0
                    ],
                    [
                        "ddd1491a-86d5-4af7-a013-89bde75528bd",
                        "ABCDEFJHI",
                        "Dell",
                        1614556800,
                        2.8,
                        64,
                        13.5,
                        "1200.99",
                        2,
                        1614564122,
                        null
                    ]
                ]
            }

        **Example unexpected response**:

        .. sourcecode:: http

            HTTP/1.1 500 Internal Server Error
            Vary: Accept
            Content-Type: text/plain

            400 Bad Request: The browser (or proxy) sent a request that this server could not
                understand.

        :query limit: Limit of how many records per page. Defaults to ``1000``.
        :query page: Page requested. Defaults to ``1``.
        :query order: Sort order. Defaults to ``KEY ASC``.
        :query restriction: Base64-encoded ``AND`` sequence of restrictions. For example, you
            could restrict as ``[{"attributeName": "computer_memory">=", "value": 32}]`` with
            this param set as ``""" "W3siYXR0cmlidXRlTmFtZSI6ICJjb21wdXRlcl9tZW1vcnkiLCAib3Bl"
     """cmF0aW9uIjo``-``gIj49IiwgInZhbHVlIjogMzJ9XQo=``. Defaults to no restriction.
        :reqheader Authorization: Bearer <OAuth2_token>
        :resheader Content-Type: text/plain, application/json
        :statuscode 200: No error.
        :statuscode 500: Unexpected error encountered. Returns the error message as a string.
    """)
    if request.method == 'GET':
        try:
            table_tuples, total_count = DJConnector.fetch_tuples(
                jwt_payload=jwt_payload,
                schema_name=request.args["schemaName"],
                table_name=request.args["tableName"],
                **{k: (int(v) if k in ('limit', 'page')
                    else (v.split(',') if k == 'order' else loads(
                        b64decode(v.encode('utf-8')).decode('utf-8'))))
                for k, v in request.args.items() if k not in ('schemaName', 'tableName')},
                )
            return dict(tuples=table_tuples, total_count=total_count)
        except Exception as e:
            return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/get_table_definition", methods=['POST'])
@protected_route
def get_table_definition(jwt_payload: dict) -> str:
    """
    Handler for ``/get_table_definition`` route.

    :param jwt_payload: Dictionary containing databaseAddress, username, and password strings.
    :type jwt_payload: dict
    :return: If successful then sends back definition for table otherwise returns error.
    :rtype: dict

    .. http:post:: /get_table_definition

        Route to get DataJoint table definition.

        **Example request**:

        .. sourcecode:: http

            POST /get_table_definition HTTP/1.1
            Host: fakeservices.datajoint.io
            Accept: application/json

            {
                "schemaName": "alpha_company",
                "tableName": "Computer"
            }

        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: text/plain

            # Computers that belong to the company
            computer_id          : uuid                     # unique id
            ---
            computer_serial      : varchar(9)               # manufacturer serial number
            computer_brand       : enum('HP','Dell')        # manufacturer brand
            computer_built       : date                     # manufactured date
            computer_processor   : double                   # processing power in GHz
            computer_memory      : int                      # RAM in GB
            computer_weight      : float                    # weight in lbs
            computer_cost        : decimal(6,2)             # purchased price
            computer_preowned    : tinyint                  # purchased as new or used
            computer_purchased   : datetime                 # purchased date and time
            computer_updates=null : time                     # scheduled daily update timeslot


        **Example unexpected response**:

        .. sourcecode:: http

            HTTP/1.1 500 Internal Server Error
            Vary: Accept
            Content-Type: text/plain

            400 Bad Request: The browser (or proxy) sent a request that this server could not
                understand.

        :reqheader Authorization: Bearer <OAuth2_token>
        :resheader Content-Type: text/plain
        :statuscode 200: No error.
        :statuscode 500: Unexpected error encountered. Returns the error message as a string.
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
def get_table_attributes(jwt_payload: dict) -> dict:
    """
    Handler for ``/get_table_attributes`` route.

    :param jwt_payload: Dictionary containing databaseAddress, username, and password strings.
    :type jwt_payload: dict
    :return: If successful then sends back dict of table attributes otherwise returns error.
    :rtype: dict

    .. http:post:: /get_table_attributes

        Route to get metadata on table attributes.

        **Example request**:

        .. sourcecode:: http

            POST /get_table_attributes HTTP/1.1
            Host: fakeservices.datajoint.io
            Accept: application/json

            {
                "schemaName": "alpha_company",
                "tableName": "Computer"
            }

        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json

            {
                "primary_attributes": [
                    [
                        "computer_id",
                        "uuid",
                        false,
                        null,
                        false
                    ]
                ],
                "secondary_attributes": [
                    [
                        "computer_serial",
                        "varchar(9)",
                        false,
                        null,
                        false
                    ],
                    [
                        "computer_brand",
                        "enum('HP','Dell')",
                        false,
                        null,
                        false
                    ],
                    [
                        "computer_built",
                        "date",
                        false,
                        null,
                        false
                    ],
                    [
                        "computer_processor",
                        "double",
                        false,
                        null,
                        false
                    ],
                    [
                        "computer_memory",
                        "int",
                        false,
                        null,
                        false
                    ],
                    [
                        "computer_weight",
                        "float",
                        false,
                        null,
                        false
                    ],
                    [
                        "computer_cost",
                        "decimal(6,2)",
                        false,
                        null,
                        false
                    ],
                    [
                        "computer_preowned",
                        "tinyint",
                        false,
                        null,
                        false
                    ],
                    [
                        "computer_purchased",
                        "datetime",
                        false,
                        null,
                        false
                    ],
                    [
                        "computer_updates",
                        "time",
                        true,
                        "null",
                        false
                    ]
                ]
            }

        **Example unexpected response**:

        .. sourcecode:: http

            HTTP/1.1 500 Internal Server Error
            Vary: Accept
            Content-Type: text/plain

            400 Bad Request: The browser (or proxy) sent a request that this server could not
                understand.

        :reqheader Authorization: Bearer <OAuth2_token>
        :resheader Content-Type: text/plain, application/json
        :statuscode 200: No error.
        :statuscode 500: Unexpected error encountered. Returns the error message as a string.
    """
    try:
        return DJConnector.get_table_attributes(jwt_payload,
                                                request.json["schemaName"],
                                                request.json["tableName"])
    except Exception as e:
        return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/record", methods=['POST'])
@protected_route
def post_record(jwt_payload: dict) -> str:
    """
    Handler for ``/insert_tuple`` route.

    :param jwt_payload: Dictionary containing databaseAddress, username, and password strings.
    :type jwt_payload: dict
    :return: If successful then returns ``Insert Successful`` otherwise returns error.
    :rtype: dict

    .. http:post:: /insert_tuple

        Route to insert a record.

        **Example request**:

        .. sourcecode:: http

            POST /insert_tuple HTTP/1.1
            Host: fakeservices.datajoint.io
            Accept: application/json

            {
                "schemaName": "alpha_company",
                "tableName": "Computer",
                "tuple": {
                    "computer_id": "ffffffff-86d5-4af7-a013-89bde75528bd",
                    "computer_serial": "ZYXWVEISJ",
                    "computer_brand": "HP",
                    "computer_built": "2021-01-01",
                    "computer_processor": 2.7,
                    "computer_memory": 32,
                    "computer_weight": 3.7,
                    "computer_cost": 599.99,
                    "computer_preowned": 0,
                    "computer_purchased": "2021-02-01 13:00:00",
                    "computer_updates": 0
                }
            }


        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: text/plain

            Insert Successful

        **Example unexpected response**:

        .. sourcecode:: http

            HTTP/1.1 500 Internal Server Error
            Vary: Accept
            Content-Type: text/plain

            400 Bad Request: The browser (or proxy) sent a request that this server could not
                understand.

        :reqheader Authorization: Bearer <OAuth2_token>
        :resheader Content-Type: text/plain
        :statuscode 200: No error.
        :statuscode 500: Unexpected error encountered. Returns the error message as a string.
    """
    if request.method == 'POST':
        try:
            # Attempt to insert
            DJConnector.insert_tuple(jwt_payload,
                                     request.args["schemaName"],
                                     request.args["tableName"],
                                     request.args["record"])
            return "Insert Successful"
        except Exception as e:
            return str(e), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/record/dependency", methods=['GET'])
@protected_route
def record_dependency(jwt_payload: dict) -> dict:
    ("""
    Handler for ``/record/dependency`` route.

    :param jwt_payload: Dictionary containing databaseAddress, username, and password strings.
    :type jwt_payload: dict
    :return: If sucessfuly sends back a list of dependencies otherwise returns error.
    :rtype: dict

    .. http:get:: /record/dependency

        Route to get the metadata in relation to the dependent records associated with a """
        """restricted subset of a table.

        **Example request**:

        .. sourcecode:: http

            GET /fetch_tuples?schemaName=alpha_company&tableName=Computer&"""
     "restriction=W3siYXR0cmlidXRlTmFtZSI6ICJjb21wdXRlcl9tZW1vcnkiLCAib3BlcmF0aW9uIjogIj49Iiw"
     "gInZhbHVlIjogMzJ9XQo="
     """ HTTP/1.1
            Host: fakeservices.datajoint.io

        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json

            {
                "dependencies": [
                    {
                        "accessible": true,
                        "count": 7,
                        "schema": "alpha_company",
                        "table": "computer"
                    },
                    {
                        "accessible": true,
                        "count": 2,
                        "schema": "alpha_company",
                        "table": "#employee"
                    }
                ]
            }

        **Example unexpected response**:

        .. sourcecode:: http

            HTTP/1.1 500 Internal Server Error
            Vary: Accept
            Content-Type: text/plain

            400 Bad Request: The browser (or proxy) sent a request that this server could not
                understand.

        :query schemaName: Schema name.
        :query tableName: Table name.
        :query restriction: Base64-encoded ``AND`` sequence of restrictions. For example, you
            could restrict as ``[{"attributeName": "computer_memory">=", "value": 32}]`` with
            this param set as ``""" "W3siYXR0cmlidXRlTmFtZSI6ICJjb21wdXRlcl9tZW1vcnkiLCAib3Bl"
     """cmF0aW9uIjo``-``gIj49IiwgInZhbHVlIjogMzJ9XQo=``.
        :reqheader Authorization: Bearer <OAuth2_token>
        :resheader Content-Type: text/plain, application/json
        :statuscode 200: No error.
        :statuscode 500: Unexpected error encountered. Returns the error message as a string.
    """)
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
def update_tuple(jwt_payload: dict) -> str:
    """
    Handler for ``/update_tuple`` route.

    :param jwt_payload: Dictionary containing databaseAddress, username, and password strings.
    :type jwt_payload: dict
    :return: If successful then returns ``Update Successful`` otherwise returns error.
    :rtype: dict

    .. http:post:: /update_tuple

        Route to update a record.

        **Example request**:

        .. sourcecode:: http

            POST /update_tuple HTTP/1.1
            Host: fakeservices.datajoint.io
            Accept: application/json

            {
                "schemaName": "alpha_company",
                "tableName": "Computer",
                "tuple": {
                    "computer_id": "ffffffff-86d5-4af7-a013-89bde75528bd",
                    "computer_serial": "ZYXWVEISJ",
                    "computer_brand": "HP",
                    "computer_built": "2021-01-01",
                    "computer_processor": 2.7,
                    "computer_memory": 32,
                    "computer_weight": 3.7,
                    "computer_cost": 399.99,
                    "computer_preowned": 0,
                    "computer_purchased": "2021-02-01 13:00:00",
                    "computer_updates": 0
                }
            }


        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: text/plain

            Update Successful

        **Example unexpected response**:

        .. sourcecode:: http

            HTTP/1.1 500 Internal Server Error
            Vary: Accept
            Content-Type: text/plain

            400 Bad Request: The browser (or proxy) sent a request that this server could not
                understand.

        :reqheader Authorization: Bearer <OAuth2_token>
        :resheader Content-Type: text/plain
        :statuscode 200: No error.
        :statuscode 500: Unexpected error encountered. Returns the error message as a string.
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
def delete_tuple(jwt_payload: dict) -> dict:
    """
    Handler for ``/delete_tuple`` route.

    :param jwt_payload: Dictionary containing databaseAddress, username, and password strings.
    :type jwt_payload: dict
    :return: If successful returns ``Delete Successful`` otherwise returns error.
    :rtype: dict

    .. http:post:: /delete_tuple

        Route to delete a specific record.

        **Example request**:

        .. sourcecode:: http

            POST /delete_tuple HTTP/1.1
            Host: fakeservices.datajoint.io
            Accept: application/json

            {
                "schemaName": "alpha_company",
                "tableName": "Computer",
                "restrictionTuple": {
                    "computer_id": "4e41491a-86d5-4af7-a013-89bde75528bd"
                }
            }

        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: text/plain

            Delete Successful

        **Example conflict response**:

        .. sourcecode:: http

            HTTP/1.1 409 Conflict
            Vary: Accept
            Content-Type: application/json

            {
                "error": "IntegrityError",
                "error_msg": "Cannot delete or update a parent row: a foreign key constraint
                    fails (`alpha_company`.`#employee`, CONSTRAINT `#employee_ibfk_1` FOREIGN
                    KEY (`computer_id`) REFERENCES `computer` (`computer_id`) ON DELETE
                    RESTRICT ON UPDATE CASCADE",
                "child_schema": "alpha_company",
                "child_table": "Employee"
            }

        **Example unexpected response**:

        .. sourcecode:: http

            HTTP/1.1 500 Internal Server Error
            Vary: Accept
            Content-Type: text/plain

            400 Bad Request: The browser (or proxy) sent a request that this server could not
                understand.

        :query cascade: Enable cascading delete. Accepts ``true`` or ``false``.
            Defaults to ``false``.
        :reqheader Authorization: Bearer <OAuth2_token>
        :resheader Content-Type: text/plain, application/json
        :statuscode 200: No error.
        :statuscode 409: Attempting to delete a record with dependents while ``cascade`` set
            to ``false``.
        :statuscode 500: Unexpected error encountered. Returns the error message as a string.
    """
    try:
        # Attempt to delete tuple
        DJConnector.delete_tuple(jwt_payload,
                                 request.json["schemaName"],
                                 request.json["tableName"],
                                 request.json["restrictionTuple"],
                                 **{k: v.lower() == 'true'
                                    for k, v in request.args.items() if k == 'cascade'},)
        return "Delete Sucessful"
    except IntegrityError as e:
        match = foreign_key_error_regexp.match(e.args[0])
        return dict(error=e.__class__.__name__,
                    error_msg=str(e),
                    child_schema=match.group('child').split('.')[0][1:-1],
                    child_table=to_camel_case(match.group('child').split('.')[1][1:-1]),
                    ), 409
    except Exception as e:
        return str(e), 500


def run():
    """
    Starts API server.
    """
    app.run(host='0.0.0.0', port=environ.get('PHARUS_PORT', 5000))


if __name__ == '__main__':
    run()
