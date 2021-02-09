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
def String(schema):
    @schema
    class String(dj.Manual):
        definition = """
        id: int
        ---
        string_attribute: varchar(32)
        """
    yield String
    String.drop()

@pytest.fixture
def Bool(schema):
    @schema
    class Bool(dj.Manual):
        definition = """
        id: int
        ---
        bool_attribute: bool
        """
    yield Bool
    Bool.drop()

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

@pytest.fixture
def ParentPart(schema):
    @schema
    class ScanData(dj.Manual):
        definition = """
        scan_id : int unsigned
        ---
        data: int unsigned
        """
        
    @schema
    class ProcessScanData(dj.Computed):
        definition = """
        -> ScanData # Forigen Key Reference
        ---
        processed_scan_data : int unsigned
        """
            
        class ProcessScanDataPart(dj.Part):
            definition = """
            -> ProcessScanData
            ---
            processed_scan_data_part : int unsigned
            """
            
            
        def make(self, key):
            scan_data_dict = (ScanData & key).fetch1()
            self.insert1(dict(key, processed_scan_data=scan_data_dict['data']))
            self.ProcessScanDataPart.insert1(
                dict(key, processed_scan_data_part=scan_data_dict['data'] * 2))

    yield dict(ScanData=ScanData, ProcessScanData=ProcessScanData)
    ScanData.drop()


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


def test_decimal(token, client, Decimal):
    validate(
        table=Decimal,
        inserted_value=6.123,
        expected_type=str,
        expected_value='6.12',
        client=client,
        token=token,
    )

def test_string(token, client, String):
    validate(
        table=String,
        inserted_value='hi',
        expected_type=str,
        expected_value='hi',
        client=client,
        token=token,
    )

def test_bool(token, client, Bool):
    validate(
        table=Bool,
        inserted_value=True,
        expected_type=Number,
        expected_value=1,
        client=client,
        token=token,
    )

def test_date(token, client, Date):
    validate(
        table=Date,
        inserted_value=date(2021, 1, 31),
        expected_type=Number,
        expected_value=1612051200,
        client=client,
        token=token,
    )


def test_datetime(token, client, Datetime):
    validate(
        table=Datetime,
        inserted_value=datetime(2021, 1, 28, 14, 20, 58),
        expected_type=Number,
        expected_value=1611843658,
        client=client,
        token=token,
    )


def test_timestamp(token, client, Timestamp):
    validate(
        table=Timestamp,
        inserted_value=datetime(2021, 1, 27, 21, 2, 31, 123),
        expected_type=Number,
        expected_value=1611781351,
        client=client,
        token=token,
    )


def test_time(token, client, Time):
    validate(
        table=Time,
        inserted_value=time(21, 1, 32),
        expected_type=Number,
        expected_value=75692.,
        client=client,
        token=token,
    )


def test_blob(token, client, Blob):
    validate(
        table=Blob,
        inserted_value=[1, 2, 3],
        expected_type=str,
        expected_value='=BLOB=',
        client=client,
        token=token,
    )


def test_longblob(token, client, Longblob):
    validate(
        table=Longblob,
        inserted_value=[4, 5, 6],
        expected_type=str,
        expected_value='=BLOB=',
        client=client,
        token=token,
    )


def test_uuid(token, client, Uuid):
    validate(
        table=Uuid,
        inserted_value=UUID('d710463dabd748858c62d0ae857e2910'),
        expected_type=str,
        expected_value='d710463d-abd7-4885-8c62-d0ae857e2910',
        client=client,
        token=token,
    )

def test_part_table(token, client, ParentPart):
    ParentPart['ScanData'].insert1(dict(scan_id=0, data=5))
    ParentPart['ProcessScanData'].populate()
    
    # Test Parent
    REST_value = client.post('/api/fetch_tuples',
                            headers=dict(Authorization=f'Bearer {token}'),
                            json=dict(schemaName='add_types',
                                        tableName=ParentPart['ProcessScanData'].__name__)).json['tuples'][0]

    assert REST_value == [0, 5]

    # Test Child
    REST_value = client.post('/api/fetch_tuples',
                            headers=dict(Authorization=f'Bearer {token}'),
                            json=dict(schemaName='add_types',
                                        tableName=ParentPart['ProcessScanData'].__name__ + '.' + 
                                        ParentPart['ProcessScanData'].ProcessScanDataPart.__name__)).json['tuples'][0]

    assert REST_value == [0, 10]
