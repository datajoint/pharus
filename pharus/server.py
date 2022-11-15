"""Exposed REST API."""
from os import environ
from .interface import _DJConnector
import datajoint as dj
from . import __version__ as version
from typing import Callable
from functools import wraps
from typing import Union
import pymysql

# Crypto libaries
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

from requests.auth import HTTPBasicAuth
from flask import Flask, request
import jwt
import requests
from json import loads
from base64 import b64decode
from datajoint.errors import IntegrityError
from datajoint.table import foreign_key_error_regexp
from datajoint.utils import to_camel_case
import traceback
import time

app = Flask(__name__)
# Check if PRIVATE_KEY and PUBIC_KEY is set, if not generate them.
# NOTE: For web deployment, please set the these enviorment variable to be the same between
# the instance
if (
    environ.get("PHARUS_PRIVATE_KEY") is None
    or environ.get("PHARUS_PUBLIC_KEY") is None
):
    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=2048
    )
    environ["PHARUS_PRIVATE_KEY"] = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption(),
    ).decode()
    environ["PHARUS_PUBLIC_KEY"] = (
        key.public_key()
        .public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH,
        )
        .decode()
    )


def protected_route(function: Callable) -> Callable:
    """
    Protected route function decorator which authenticates requests.

    :param function: Function to decorate, typically routes
    :type function: :class:`~typing.Callable`
    :return: Function output if JWT authetication is successful, otherwise return error
        message
    :rtype: :class:`~typing.Callable`
    """

    @wraps(function)
    def wrapper(**kwargs):
        try:
            if "database_host" in request.args:
                encoded_jwt = request.headers.get("Authorization").split()[1]
                connect_creds = {
                    "databaseAddress": request.args["database_host"],
                    "username": jwt.decode(
                        encoded_jwt,
                        crypto_serialization.load_der_public_key(
                            b64decode(environ.get("PHARUS_OIDC_PUBLIC_KEY").encode())
                        ),
                        algorithms="RS256",
                        options=dict(verify_aud=False),
                    )[environ.get("PHARUS_OIDC_SUBJECT_KEY")],
                    "password": encoded_jwt,
                }
            else:
                connect_creds = jwt.decode(
                    request.headers.get("Authorization").split()[1],
                    environ["PHARUS_PUBLIC_KEY"],
                    algorithms="RS256",
                )
            connection = dj.Connection(
                host=connect_creds["databaseAddress"],
                user=connect_creds["username"],
                password=connect_creds["password"],
            )
            return function(connection, **kwargs)
        except Exception as e:
            return str(e), 401

    wrapper.__name__ = function.__name__
    return wrapper


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/version", methods=["GET"])
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
            Content-Type: application/json

            {
                "version": "0.6.3"
            }

        :statuscode 200: No error.
    """
    if request.method in {"GET", "HEAD"}:
        return dict(version=version)


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/login", methods=["POST"])
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

    :return: Function output is an encoded JWT if successful, otherwise return error message
    :rtype: dict

    .. http:post:: /login

        Route to generate an authentication token.

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
    if request.method == "POST":
        # Try to login in with the database connection info, if true then create jwt key
        try:
            if "database_host" in request.args:
                # Oidc token exchange

                body = {
                    "grant_type": "authorization_code",
                    "code": request.args["code"],
                    "code_verifier": environ.get("PHARUS_OIDC_CODE_VERIFIER"),
                    "client_id": environ.get("PHARUS_OIDC_CLIENT_ID"),
                    "redirect_uri": environ.get("PHARUS_OIDC_REDIRECT_URI"),
                }
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                }
                auth = HTTPBasicAuth(
                    environ.get("PHARUS_OIDC_CLIENT_ID"),
                    environ.get("PHARUS_OIDC_CLIENT_SECRET"),
                )
                result = requests.post(
                    environ.get("PHARUS_OIDC_TOKEN_URL"),
                    data=body,
                    headers=headers,
                    auth=auth,
                )
                auth_info = dict(
                    jwt=result.json()["access_token"], id=result.json()["id_token"]
                )
                time.sleep(1)
                connect_creds = {
                    "databaseAddress": request.args["database_host"],
                    "username": jwt.decode(
                        auth_info["jwt"],
                        crypto_serialization.load_der_public_key(
                            b64decode(environ.get("PHARUS_OIDC_PUBLIC_KEY").encode())
                        ),
                        algorithms="RS256",
                        options=dict(verify_aud=False),
                    )[environ.get("PHARUS_OIDC_SUBJECT_KEY")],
                    "password": auth_info["jwt"],
                }
            else:  # Database login
                # Generate JWT key and send it back
                auth_info = dict(
                    jwt=jwt.encode(
                        request.json, environ["PHARUS_PRIVATE_KEY"], algorithm="RS256"
                    )
                )
                connect_creds = request.json
            if connect_creds.keys() < {"databaseAddress", "username", "password"}:
                return dict(error="Invalid Request, check headers and/or json body")
            try:
                dj.Connection(
                    host=connect_creds["databaseAddress"],
                    user=connect_creds["username"],
                    password=connect_creds["password"],
                )
            except pymysql.err.OperationalError as e:
                if (
                    (root_host := environ.get("DJ_HOST"))
                    and (root_user := environ.get("DJ_ROOT_USER"))
                    and (root_password := environ.get("DJ_ROOT_PASS"))
                ):
                    dj.Connection(
                        host=root_host,
                        user=root_user,
                        password=root_password,
                    ).query("FLUSH PRIVILEGES")
                    dj.Connection(
                        host=connect_creds["databaseAddress"],
                        user=connect_creds["username"],
                        password=connect_creds["password"],
                    )
                else:
                    raise e
            return dict(**auth_info)
        except Exception:
            return traceback.format_exc(), 500


@app.route(f"{environ.get('PHARUS_PREFIX', '')}/schema", methods=["GET"])
@protected_route
def schema(connection: dj.Connection) -> dict:
    """
    Handler for ``/schema`` route.

    :param connection: User's DataJoint connection object
    :type connection: dj.Connection
    :return: If successful then sends back a list of schemas names otherwise returns error.
    :rtype: dict

    .. http:get:: /schema

        Route to get list of schemas.

        **Example request**:

        .. sourcecode:: http

            GET /schema HTTP/1.1
            Host: fakeservices.datajoint.io
            Authorization: Bearer <token>

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
    if request.method in {"GET", "HEAD"}:
        # Get all the schemas
        try:
            schemas_name = _DJConnector._list_schemas(connection)
            return dict(schemaNames=schemas_name)
        except Exception:
            return traceback.format_exc(), 500


@app.route(
    f"{environ.get('PHARUS_PREFIX', '')}/schema/<schema_name>/table", methods=["GET"]
)
@protected_route
def table(
    connection: dj.Connection,
    schema_name: str,
) -> dict:
    """
    Handler for ``/schema/{schema_name}/table`` route.

    :param connection: User's DataJoint connection object
    :type connection: dj.Connection
    :param schema_name: Schema name.
    :type schema_name: str
    :return: If successful then sends back a list of table names otherwise returns error.
    :rtype: dict

    .. http:get:: /schema/{schema_name}/table

        Route to get tables within a schema.

        **Example request**:

        .. sourcecode:: http

            GET /schema/alpha_company/table HTTP/1.1
            Host: fakeservices.datajoint.io
            Authorization: Bearer <token>

        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json

            {
                "tableTypes": {
                    "computed": [],
                    "imported": [],
                    "lookup": [
                        "Employee"
                    ],
                    "manual": [
                        "Computer"
                    ],
                    "part": []
                }
            }

        **Example unexpected response**:

        .. sourcecode:: http

            HTTP/1.1 500 Internal Server Error
            Vary: Accept
            Content-Type: text/plain

            400 Bad Request: The browser (or proxy) sent a request that this server could not
                understand.

        :query schema_name: Schema name.
        :reqheader Authorization: Bearer <OAuth2_token>
        :resheader Content-Type: text/plain, application/json
        :statuscode 200: No error.
        :statuscode 500: Unexpected error encountered. Returns the error message as a string.
    """
    if request.method in {"GET", "HEAD"}:
        try:
            tables_dict_list = _DJConnector._list_tables(connection, schema_name)
            return dict(tableTypes=tables_dict_list)
        except Exception:
            return traceback.format_exc(), 500


@app.route(
    f"{environ.get('PHARUS_PREFIX', '')}/schema/<schema_name>/table/<table_name>/record",
    methods=["GET", "POST", "PATCH", "DELETE"],
)
@protected_route
def record(
    connection: dj.Connection,
    schema_name: str,
    table_name: str,
) -> Union[dict, str, tuple]:
    (
        """
        Handler for ``/schema/{schema_name}/table/{table_name}/record`` route.

        :param connection: User's DataJoint connection object
        :type connection: dj.Connection
        :param schema_name: Schema name.
        :type schema_name: str
        :param table_name: Table name.
        :type table_name: str
        :return: If successful performs desired operation based on HTTP method, otherwise
            returns error.
        :rtype: :class:`~typing.Union[dict, str, tuple]`

        .. http:get:: /schema/{schema_name}/table/{table_name}/record

            Route to fetch records.

            **Example request**:

            .. sourcecode:: http

                GET /schema/alpha_company/table/Computer/record?limit=1&page=2&"""
        "order=computer_id%20DESC&restriction=W3siYXR0cmlidXRlTmFtZSI6ICJjb21wdXRlcl9tZW1vcnk"
        "iLCAib3BlcmF0aW9uIjogIj49IiwgInZhbHVlIjogMTZ9XQo="
        """ HTTP/1.1
                Host: fakeservices.datajoint.io
                Authorization: Bearer <token>

            **Example successful response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "recordHeader": [
                        "computer_id",
                        "computer_serial",
                        "computer_brand",
                        "computer_built",
                        "computer_processor",
                        "computer_memory",
                        "computer_weight",
                        "computer_cost",
                        "computer_preowned",
                        "computer_purchased",
                        "computer_updates",
                        "computer_accessories"
                    ],
                    "records": [
                        [
                            "4e41491a-86d5-4af7-a013-89bde75528bd",
                            "DJS1JA17G",
                            "Dell",
                            1590364800,
                            2.2,
                            16,
                            4.4,
                            "700.99",
                            0,
                            1603181061,
                            null,
                            "=BLOB="
                        ]
                    ],
                    "totalCount": 2
                }

            **Example unexpected response**:

            .. sourcecode:: http

                HTTP/1.1 500 Internal Server Error
                Vary: Accept
                Content-Type: text/plain

                400 Bad Request: The browser (or proxy) sent a request that this server could
                    not understand.

            :query schema_name: Schema name.
            :query table_name: Table name.
            :query limit: Limit of how many records per page. Defaults to ``1000``.
            :query page: Page requested. Defaults to ``1``.
            :query order: Sort order. Defaults to ``KEY ASC``.
            :query restriction: Base64-encoded ``AND`` sequence of restrictions. For example,
                you could restrict as ``[{"attributeName": "computer_memory", "operation": ``-
                ``">=", "value": 16}]`` with this param set as
                ``W3siYXR0cmlidXRlTmFtZSI6ICJjb21wdXRlcl9tZW1vcnkiLCAib3Bl``-
                ``cmF0aW9uIjogIj49IiwgInZhbHVlIjogMTZ9XQo=``. Defaults to no restriction.
            :reqheader Authorization: Bearer <OAuth2_token>
            :resheader Content-Type: text/plain, application/json
            :statuscode 200: No error.
            :statuscode 500: Unexpected error encountered. Returns the error message as a
                string.

        .. http:post:: /schema/{schema_name}/table/{table_name}/record

            Route to insert a record. Omitted attributes utilize the default if set.

            **Example request**:

            .. sourcecode:: http

                POST /schema/alpha_company/table/Computer/record HTTP/1.1
                Host: fakeservices.datajoint.io
                Accept: application/json
                Authorization: Bearer <token>

                {
                    "records": [
                        {
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
                    ]
                }

            **Example successful response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: text/plain

                {
                    "response": "Insert Successful"
                }

            **Example unexpected response**:

            .. sourcecode:: http

                HTTP/1.1 500 Internal Server Error
                Vary: Accept
                Content-Type: text/plain

                400 Bad Request: The browser (or proxy) sent a request that this server could
                    not understand.

            :reqheader Authorization: Bearer <OAuth2_token>
            :resheader Content-Type: text/plain
            :statuscode 200: No error.
            :statuscode 500: Unexpected error encountered. Returns the error message as a
                string.

        .. http:patch:: /schema/{schema_name}/table/{table_name}/record

            Route to update a record. Omitted attributes utilize the default if set.

            **Example request**:

            .. sourcecode:: http

                PATCH /schema/alpha_company/table/Computer/record HTTP/1.1
                Host: fakeservices.datajoint.io
                Accept: application/json
                Authorization: Bearer <token>

                {
                    "records": [
                        {
                            "computer_id": "ffffffff-86d5-4af7-a013-89bde75528bd",
                            "computer_serial": "ZYXWVEISJ",
                            "computer_brand": "HP",
                            "computer_built": "2021-01-01",
                            "computer_processor": 2.7,
                            "computer_memory": 32,
                            "computer_weight": 3.7,
                            "computer_cost": 601.01,
                            "computer_preowned": 0,
                            "computer_purchased": "2021-02-01 13:00:00",
                            "computer_updates": 0
                        }
                    ]
                }

            **Example successful response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: text/plain

                {
                    "response": "Update Successful"
                }

            **Example unexpected response**:

            .. sourcecode:: http

                HTTP/1.1 500 Internal Server Error
                Vary: Accept
                Content-Type: text/plain

                400 Bad Request: The browser (or proxy) sent a request that this server could
                    not understand.

            :reqheader Authorization: Bearer <OAuth2_token>
            :resheader Content-Type: text/plain
            :statuscode 200: No error.
            :statuscode 500: Unexpected error encountered. Returns the error message as a
                string.

        .. http:delete:: /schema/{schema_name}/table/{table_name}/record

            Route to delete a specific record.

            **Example request**:

            .. sourcecode:: http

                DELETE /schema/alpha_company/table/Computer/record?cascade=false&"""
        "restriction=W3siYXR0cmlidXRlTmFtZSI6ICJjb21wdXRlcl9tZW1vcnkiLCAib3BlcmF0aW9uIjogIj49"
        "IiwgInZhbHVlIjogMTZ9XQo="
        """ HTTP/1.1
                Host: fakeservices.datajoint.io
                Authorization: Bearer <token>

            **Example successful response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: text/plain

                {
                    "response": "Delete Successful"
                }

            **Example conflict response**:

            .. sourcecode:: http

                HTTP/1.1 409 Conflict
                Vary: Accept
                Content-Type: application/json

                {
                    "error": "IntegrityError",
                    "error_msg": "Cannot delete or update a parent row: a foreign key
                        constraint fails (`alpha_company`.`#employee`, CONSTRAINT
                        `#employee_ibfk_1` FOREIGN KEY (`computer_id`) REFERENCES `computer`
                        (`computer_id`) ON DELETE RESTRICT ON UPDATE CASCADE",
                    "child_schema": "alpha_company",
                    "child_table": "Employee"
                }

            **Example unexpected response**:

            .. sourcecode:: http

                HTTP/1.1 500 Internal Server Error
                Vary: Accept
                Content-Type: text/plain

                400 Bad Request: The browser (or proxy) sent a request that this server could
                    not understand.

            :query cascade: Enable cascading delete. Accepts ``true`` or ``false``.
                Defaults to ``false``.
            :query restriction: Base64-encoded ``AND`` sequence of restrictions. For example,
                you could restrict as ``[{"attributeName": "computer_memory", "operation": ``-
                ``">=", "value": 16}]`` with this param set as
                ``W3siYXR0cmlidXRlTmFtZSI6ICJjb21wdXRlcl9tZW1vcnkiLCAib3Bl``-
                ``cmF0aW9uIjogIj49IiwgInZhbHVlIjogMTZ9XQo=``. Defaults to no restriction.
            :reqheader Authorization: Bearer <OAuth2_token>
            :resheader Content-Type: text/plain, application/json
            :statuscode 200: No error.
            :statuscode 409: Attempting to delete a record with dependents while ``cascade``
                set to ``false``.
            :statuscode 500: Unexpected error encountered. Returns the error message as a
                string.
        """
    )
    if request.method in {"GET", "HEAD"}:
        try:
            schema_virtual_module = dj.VirtualModule(
                schema_name, schema_name, connection=connection
            )

            # Get table object from name
            dj_table = _DJConnector._get_table_object(schema_virtual_module, table_name)

            record_header, table_tuples, total_count = _DJConnector._fetch_records(
                query=dj_table,
                **{
                    k: int(v) for k, v in request.args.items() if k in ("limit", "page")
                },
                **{
                    k: loads(b64decode(v.encode("utf-8")).decode("utf-8"))
                    for k, v in request.args.items()
                    if k == "restriction"
                },
                **{k: v.split(",") for k, v in request.args.items() if k == "order"},
            )
            return dict(
                recordHeader=record_header, records=table_tuples, totalCount=total_count
            )
        except Exception:
            return traceback.format_exc(), 500
    elif request.method == "POST":
        try:
            _DJConnector._insert_tuple(
                connection, schema_name, table_name, request.json["records"]
            )
            return {"response": "Insert Successful"}
        except Exception:
            return traceback.format_exc(), 500
    elif request.method == "PATCH":
        try:
            _DJConnector._update_tuple(
                connection, schema_name, table_name, request.json["records"]
            )
            return {"response": "Update Successful"}
        except Exception:
            return traceback.format_exc(), 500
    elif request.method == "DELETE":
        try:
            _DJConnector._delete_records(
                connection,
                schema_name,
                table_name,
                **{
                    k: loads(b64decode(v.encode("utf-8")).decode("utf-8"))
                    for k, v in request.args.items()
                    if k == "restriction"
                },
                **{
                    k: v.lower() == "true"
                    for k, v in request.args.items()
                    if k == "cascade"
                },
            )
            return {"response": "Delete Successful"}
        except IntegrityError as e:
            match = foreign_key_error_regexp.match(e.args[0])
            return (
                dict(
                    error=e.__class__.__name__,
                    errorMessage=str(e),
                    childSchema=match.group("child").split(".")[0][1:-1],
                    childTable=to_camel_case(match.group("child").split(".")[1][1:-1]),
                ),
                409,
            )
        except Exception:
            return traceback.format_exc(), 500


@app.route(
    f"{environ.get('PHARUS_PREFIX', '')}/schema/<schema_name>/table/<table_name>/definition",
    methods=["GET"],
)
@protected_route
def definition(
    connection: dj.Connection,
    schema_name: str,
    table_name: str,
) -> str:
    """
    Handler for ``/schema/{schema_name}/table/{table_name}/definition`` route.

    :param connection: User's DataJoint connection object
    :type connection: dj.Connection
    :param schema_name: Schema name.
    :type schema_name: str
    :param table_name: Table name.
    :type table_name: str
    :return: If successful then sends back definition for table otherwise returns error.
    :rtype: str

    .. http:get:: /schema/{schema_name}/table/{table_name}/definition

        Route to get DataJoint table definition.

        **Example request**:

        .. sourcecode:: http

            GET /schema/alpha_company/table/Computer/definition HTTP/1.1
            Host: fakeservices.datajoint.io
            Authorization: Bearer <token>

        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: text/plain

            # Computers that belong to the company
            computer_id          : uuid                      # unique id
            ---
            computer_serial="ABC101" : varchar(9)            # manufacturer serial number
            computer_brand       : enum('HP','Dell')         # manufacturer brand
            computer_built       : date                      # manufactured date
            computer_processor   : double                    # processing power in GHz
            computer_memory      : int                       # RAM in GB
            computer_weight      : float                     # weight in lbs
            computer_cost        : decimal(6,2)              # purchased price
            computer_preowned    : tinyint                   # purchased as new or used
            computer_purchased   : datetime                  # purchased date and time
            computer_updates=null : time                     # scheduled daily update timeslot
            computer_accessories=null : longblob             # included additional accessories

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
    if request.method in {"GET", "HEAD"}:
        try:
            table_definition = _DJConnector._get_table_definition(
                connection, schema_name, table_name
            )
            return table_definition
        except Exception:
            return traceback.format_exc(), 500


@app.route(
    f"{environ.get('PHARUS_PREFIX', '')}/schema/<schema_name>/table/<table_name>/attribute",
    methods=["GET"],
)
@protected_route
def attribute(
    connection: dj.Connection,
    schema_name: str,
    table_name: str,
) -> dict:
    """
    Handler for ``/schema/{schema_name}/table/{table_name}/attribute`` route.

    :param connection: User's DataJoint connection object
    :type connection: dj.Connection
    :param schema_name: Schema name.
    :type schema_name: str
    :param table_name: Table name.
    :type table_name: str
    :return: If successful then sends back dict of table attributes otherwise returns error.
    :rtype: dict

    .. http:GET:: /schema/{schema_name}/table/{table_name}/attribute

        Route to get metadata on table attributes.

        **Example request**:

        .. sourcecode:: http

            GET /schema/alpha_company/table/Computer/attribute HTTP/1.1
            Host: fakeservices.datajoint.io
            Authorization: Bearer <token>

        **Example successful response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json

            {
                "attributeHeader": [
                    "name",
                    "type",
                    "nullable",
                    "default",
                    "autoincrement"
                ],
                "attributes": {
                    "primary": [
                        [
                            "computer_id",
                            "uuid",
                            false,
                            null,
                            false
                        ]
                    ],
                    "secondary": [
                        [
                            "computer_serial",
                            "varchar(9)",
                            false,
                            "\"ABC101\"",
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
                        ],
                        [
                            "computer_accessories",
                            "longblob",
                            true,
                            "null",
                            false
                        ]
                    ]
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
    if request.method in {"GET", "HEAD"}:
        try:
            local_values = locals()
            local_values[schema_name] = dj.VirtualModule(
                schema_name, schema_name, connection=connection
            )

            # Get table object from name
            dj_table = _DJConnector._get_table_object(
                local_values[schema_name], table_name
            )

            attributes_meta = _DJConnector._get_attributes(dj_table)
            return dict(
                attributeHeaders=attributes_meta["attribute_headers"],
                attributes=attributes_meta["attributes"],
            )
        except Exception:
            return traceback.format_exc(), 500


@app.route(
    f"{environ.get('PHARUS_PREFIX', '')}/schema/<schema_name>/table/<table_name>/dependency",
    methods=["GET"],
)
@protected_route
def dependency(
    connection: dj.Connection,
    schema_name: str,
    table_name: str,
) -> dict:
    (
        """
        Handler for ``/schema/{schema_name}/table/{table_name}/dependency`` route.

        :param connection: User's DataJoint connection object
        :type connection: dj.Connection
        :param schema_name: Schema name.
        :type schema_name: str
        :param table_name: Table name.
        :type table_name: str
        :return: If sucessfuly sends back a list of dependencies otherwise returns error.
        :rtype: dict

        .. http:get:: /schema/{schema_name}/table/{table_name}/dependency

            Route to get the metadata in relation to the dependent records associated with """
        """a restricted subset of a table.

            **Example request**:

            .. sourcecode:: http

                GET /schema/alpha_company/table/Computer/dependency?restriction=W3siYXR0cml"""
        "idXRlTmFtZSI6ICJjb21wdXRlcl9tZW1vcnkiLCAib3BlcmF0aW9uIjogIj49IiwgInZhbHVlIjogMTZ9XQo"
        "="
        """ HTTP/1.1
                Host: fakeservices.datajoint.io
                Authorization: Bearer <token>

            **Example successful response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "dependencies": [
                        {
                            "accessible": true,
                            "count": 2,
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

                400 Bad Request: The browser (or proxy) sent a request that this server could
                    not understand.

            :query schema_name: Schema name.
            :query table_name: Table name.
            :query restriction: Base64-encoded ``AND`` sequence of restrictions. For example,
                you could restrict as ``[{"attributeName": "computer_memory", "operation": ``-
                ``">=", "value": 16}]`` with this param set as
                ``W3siYXR0cmlidXRlTmFtZSI6ICJjb21wdXRlcl9tZW1vcnkiLCAib3Bl``-
                ``cmF0aW9uIjogIj49IiwgInZhbHVlIjogMTZ9XQo=``. Defaults to no restriction.
            :reqheader Authorization: Bearer <OAuth2_token>
            :resheader Content-Type: text/plain, application/json
            :statuscode 200: No error.
            :statuscode 500: Unexpected error encountered. Returns the error message as a
                string.
        """
    )
    if request.method in {"GET", "HEAD"}:
        # Get dependencies
        try:
            dependencies = _DJConnector._record_dependency(
                connection,
                schema_name,
                table_name,
                loads(
                    b64decode(request.args.get("restriction").encode("utf-8")).decode(
                        "utf-8"
                    )
                ),
            )
            return dict(dependencies=dependencies)
        except Exception:
            return traceback.format_exc(), 500


def run():
    """
    Starts API server.
    """
    app.run(host="0.0.0.0", port=environ.get("PHARUS_PORT", 5000), threaded=False)


if __name__ == "__main__":
    run()
