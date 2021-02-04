from os import getenv
import pytest
from dj_gui_api_server.DJGUIAPIServer import app
import datajoint as dj
from datetime import date, datetime, time
from numbers import Number
from uuid import UUID


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


@pytest.fixture
def token(client):
    yield client.post('/api/login', json=dict(databaseAddress=getenv('TEST_DB_SERVER'),
                                              username=getenv('TEST_DB_USER'),
                                              password=getenv('TEST_DB_PASS'))).json['jwt']


@pytest.fixture
def connection():
    dj.config['safemode'] = False
    connection = dj.conn(host=getenv('TEST_DB_SERVER'),
                         user=getenv('TEST_DB_USER'),
                         password=getenv('TEST_DB_PASS'), reset=True)
    yield connection
    dj.config['safemode'] = True
    connection.close()


@pytest.fixture
def schema(connection):
    schema = dj.Schema('add_types', connection=connection)
    yield schema
    schema.drop()


@pytest.fixture
def Int(schema):
    @schema
    class Int(dj.Manual):
        definition = """
        id: int
        ---
        int_attribute: int
        """
    yield Int
    Int.drop()


@pytest.fixture
def Float(schema):
    @schema
    class Float(dj.Manual):
        definition = """
        id: int
        ---
        float_attribute: float
        """
    yield Float
    Float.drop()


@pytest.fixture
def Decimal(schema):
    @schema
    class Decimal(dj.Manual):
        definition = """
        id: int
        ---
        decimal_attribute: decimal(5, 2)
        """
    yield Decimal
    Decimal.drop()


@pytest.fixture
def Date(schema):
    @schema
    class Date(dj.Manual):
        definition = """
        id: int
        ---
        date_attribute: date
        """
    yield Date
    Date.drop()


@pytest.fixture
def Datetime(schema):
    @schema
    class Datetime(dj.Manual):
        definition = """
        id: int
        ---
        datetime_attribute: datetime
        """
    yield Datetime
    Datetime.drop()


@pytest.fixture
def Timestamp(schema):
    @schema
    class Timestamp(dj.Manual):
        definition = """
        id: int
        ---
        timestamp_attribute: timestamp
        """
    yield Timestamp
    Timestamp.drop()


@pytest.fixture
def Time(schema):
    @schema
    class Time(dj.Manual):
        definition = """
        id: int
        ---
        time_attribute: time
        """
    yield Time
    Time.drop()


@pytest.fixture
def Blob(schema):
    @schema
    class Blob(dj.Manual):
        definition = """
        id: int
        ---
        blob_attribute: blob
        """
    yield Blob
    Blob.drop()


@pytest.fixture
def Longblob(schema):
    @schema
    class Longblob(dj.Manual):
        definition = """
        id: int
        ---
        longblob_attribute: longblob
        """
    yield Longblob
    Longblob.drop()


@pytest.fixture
def Uuid(schema):
    @schema
    class Uuid(dj.Manual):
        definition = """
        id: int
        ---
        uuid_attribute: uuid
        """
    yield Uuid
    Uuid.drop()


def validate(table, inserted_value, expected_type, expected_value, client, token):
    table.insert([(1, inserted_value)])
    _, REST_value = client.post('/api/fetch_tuples',
                                headers=dict(Authorization=f'Bearer {token}'),
                                json=dict(schemaName='add_types',
                                          tableName=table.__name__)).json['tuples'][0]
    assert isinstance(REST_value, expected_type) and REST_value == expected_value


def test_int(token, client, Int):
    validate(
        table=Int,
        inserted_value=10,
        expected_type=Number,
        expected_value=10,
        client=client,
        token=token,
    )


def test_float(token, client, Float):
    validate(
        table=Float,
        inserted_value=20.894,
        expected_type=Number,
        expected_value=20.894,
        client=client,
        token=token,
    )


# def test_decimal(token, client, Decimal):
#     validate(
#         table=Decimal,
#         inserted_value=6.123,
#         expected_type=Number,
#         expected_value=6.123,
#         client=client,
#         token=token,
#     )


def test_date(token, client, Date):
    validate(
        table=Date,
        inserted_value=date(2021, 1, 31),
        expected_type=str,
        expected_value='Sun, 31 Jan 2021 00:00:00 GMT',
        client=client,
        token=token,
    )


def test_datetime(token, client, Datetime):
    validate(
        table=Datetime,
        inserted_value=datetime(2021, 1, 28, 14, 20, 58),
        expected_type=str,
        expected_value='Thu, 28 Jan 2021 14:20:58 GMT',
        client=client,
        token=token,
    )


def test_timestamp(token, client, Timestamp):
    validate(
        table=Timestamp,
        inserted_value=datetime(2021, 1, 27, 21, 2, 31, 123),
        expected_type=str,
        expected_value='Wed, 27 Jan 2021 21:02:31 GMT',
        client=client,
        token=token,
    )


# def test_time(token, client, Time):
#     validate(
#         table=Time,
#         inserted_value=time(21, 1, 32),
#         expected_type=str,
#         expected_value='21:01:32',
#         client=client,
#         token=token,
#     )


# def test_blob(token, client, Blob):
#     validate(
#         table=Blob,
#         inserted_value=[1, 2, 3],
#         expected_type=str,
#         expected_value='=BLOB=',
#         client=client,
#         token=token,
#     )


# def test_longblob(token, client, Longblob):
#     validate(
#         table=Longblob,
#         inserted_value=[4, 5, 6],
#         expected_type=str,
#         expected_value='=BLOB=',
#         client=client,
#         token=token,
#     )


def test_uuid(token, client, Uuid):
    validate(
        table=Uuid,
        inserted_value=UUID('d710463dabd748858c62d0ae857e2910'),
        expected_type=str,
        expected_value='d710463d-abd7-4885-8c62-d0ae857e2910',
        client=client,
        token=token,
    )
