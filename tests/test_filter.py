from json import dumps
from base64 import b64encode
from urllib.parse import urlencode
from datetime import date, datetime
from . import token, client, connection, schema_main, Student, Computer


def test_filters(token, client, Student):
    # 'between' dates
    restriction = [dict(attributeName='student_enroll_date', operation='>',
                        value='2021-01-07'),
                   dict(attributeName='student_enroll_date', operation='<',
                        value='2021-01-17')]
    encoded_restriction = b64encode(dumps(restriction).encode('utf-8')).decode('utf-8')
    q = dict(limit=10, page=1, order='student_enroll_date DESC',
             restriction=encoded_restriction)
    REST_records = client.get(
        f'/schema/{Student.database}/table/{"Student"}/record?{urlencode(q)}',
        headers=dict(Authorization=f'Bearer {token}')).json['records']
    assert len(REST_records) == 10
    assert REST_records[0][3] == datetime(2021, 1, 16).timestamp()
    # 'equal' null
    restriction = [dict(attributeName='student_parking_lot', operation='=', value=None)]
    encoded_restriction = b64encode(dumps(restriction).encode('utf-8')).decode('utf-8')
    q = dict(limit=10, page=2, order='student_id ASC',
             restriction=encoded_restriction)
    REST_records = client.get(
        f'/schema/{Student.database}/table/{"Student"}/record?{urlencode(q)}',
        headers=dict(Authorization=f'Bearer {token}')).json['records']
    assert len(REST_records) == 10
    assert all([r[5] is None for r in REST_records])
    assert REST_records[0][0] == 34
    # not equal int
    restriction = [dict(attributeName='student_id', operation='!=', value='2')]
    encoded_restriction = b64encode(dumps(restriction).encode('utf-8')).decode('utf-8')
    q = dict(limit=10, page=1, order='student_id ASC',
             restriction=encoded_restriction)
    REST_records = client.get(
        f'/schema/{Student.database}/table/{"Student"}/record?{urlencode(q)}',
        headers=dict(Authorization=f'Bearer {token}')).json['records']
    assert len(REST_records) == 10
    assert all([r[0] != 2 for r in REST_records])
    assert REST_records[-1][0] == 10
    # equal 'Norma Fisher' and in_state student (bool)
    restriction = [dict(attributeName='student_name', operation='=', value='Norma Fisher'),
                   dict(attributeName='student_out_of_state', operation='=', value='0')]
    encoded_restriction = b64encode(dumps(restriction).encode('utf-8')).decode('utf-8')
    q = dict(limit=10, page=1, order='student_id ASC',
             restriction=encoded_restriction)
    REST_records = client.get(
        f'/schema/{Student.database}/table/{"Student"}/record?{urlencode(q)}',
        headers=dict(Authorization=f'Bearer {token}')).json['records']
    assert len(REST_records) == 1
    assert REST_records[0][1] == 'Norma Fisher'
    assert REST_records[0][6] == 0


def test_uuid_filter(token, client, Computer):
    """Verify UUID can be properly restricted."""
    restriction = [dict(attributeName='computer_id', operation='=',
                        value='aaaaaaaa-86d5-4af7-a013-89bde75528bd')]
    encoded_restriction = b64encode(dumps(restriction).encode('utf-8')).decode('utf-8')
    q = dict(limit=10, page=1, order='computer_id DESC',
             restriction=encoded_restriction)
    REST_records = client.get(
        f'/schema/{Computer.database}/table/{"Computer"}/record?{urlencode(q)}',
        headers=dict(Authorization=f'Bearer {token}')).json['records']
    assert len(REST_records) == 1
    assert REST_records[0][1] == 'DELL'
