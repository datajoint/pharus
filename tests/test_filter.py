from os import getenv
import pytest
from dj_gui_api_server.DJGUIAPIServer import app
import datajoint as dj
from json import dumps
from base64 import b64encode
from urllib.parse import urlencode
from datetime import date, datetime
from random import randint, choice, seed
from faker import Faker # pip install Faker
faker = Faker()
Faker.seed(0) # Pin down randomizer between runs
seed('lock')


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
def virtual_module():
    dj.config['safemode'] = False
    connection = dj.conn(host=getenv('TEST_DB_SERVER'),
                         user=getenv('TEST_DB_USER'),
                         password=getenv('TEST_DB_PASS'), reset=True)
    schema = dj.Schema('filter')

    @schema
    class Student(dj.Lookup):
        definition = """
        student_id: int
        ---
        student_name: varchar(50)
        student_ssn: varchar(20)
        student_enroll_date: datetime
        student_balance: float
        student_parking_lot=null : varchar(20)
        """
        contents = [(i, faker.name(), faker.ssn(), faker.date_between_dates(
                        date_start=date(2021, 1, 1), date_end=date(2021, 1, 31)),
                     round(randint(1000, 3000), 2),
                     choice([None, 'LotA', 'LotB', 'LotC'])) for i in range(100)]

    yield dj.VirtualModule('filter', 'filter')
    schema.drop()
    connection.close()
    dj.config['safemode'] = True


def test_filters(token, client, virtual_module):
    # 'between' dates
    restriction = [dict(attributeName='student_enroll_date', operation='>',
                        value='2021-01-07'),
                   dict(attributeName='student_enroll_date', operation='<',
                        value='2021-01-17')]
    encoded_restriction = b64encode(dumps(restriction).encode('utf-8')).decode('utf-8')
    q = dict(limit=10, page=1, order='student_enroll_date DESC',
             restriction=encoded_restriction)
    REST_records = client.post(f'/api/fetch_tuples?{urlencode(q)}',
                               headers=dict(Authorization=f'Bearer {token}'),
                               json=dict(schemaName='filter',
                                         tableName='Student')).json['tuples']
    assert len(REST_records) == 10
    assert REST_records[0][3] == datetime(2021, 1, 16).timestamp()
    # 'equal' null
    restriction = [dict(attributeName='student_parking_lot', operation='=', value=None)]
    encoded_restriction = b64encode(dumps(restriction).encode('utf-8')).decode('utf-8')
    q = dict(limit=10, page=2, order='student_id ASC',
             restriction=encoded_restriction)
    REST_records = client.post(f'/api/fetch_tuples?{urlencode(q)}',
                               headers=dict(Authorization=f'Bearer {token}'),
                               json=dict(schemaName='filter',
                                         tableName='Student')).json['tuples']
    assert len(REST_records) == 10
    assert all([r[5] is None for r in REST_records])
    assert REST_records[0][0] == 41
    # not equal int
    restriction = [dict(attributeName='student_id', operation='!=', value=2)]
    encoded_restriction = b64encode(dumps(restriction).encode('utf-8')).decode('utf-8')
    q = dict(limit=10, page=1, order='student_id ASC',
             restriction=encoded_restriction)
    REST_records = client.post(f'/api/fetch_tuples?{urlencode(q)}',
                               headers=dict(Authorization=f'Bearer {token}'),
                               json=dict(schemaName='filter',
                                         tableName='Student')).json['tuples']
    assert len(REST_records) == 10
    assert all([r[0] != 2 for r in REST_records])
    assert REST_records[-1][0] == 10
