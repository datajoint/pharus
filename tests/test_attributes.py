from . import (client, token, connection, schema_main,
               Int, Float, Decimal, String, Bool, Date, Datetime, Timestamp, Time, Blob,
               Longblob, Uuid, ParentPart)
from datetime import date, datetime, time
from numbers import Number
from uuid import UUID


def validate(table, inserted_value, expected_type, expected_value, client, token):
    REST_records = client.get(f'/schema/{table.database}/table/{table.__name__}/record',
                              headers=dict(Authorization=f'Bearer {token}')
                              ).json['records']
    assert len(REST_records) == 0
    REST_response = client.post(f'/schema/{table.database}/table/{table.__name__}/record',
                                headers=dict(Authorization=f'Bearer {token}'),
                                json=dict(records=[{
                                    'id': 1,
                                    f'{table.__name__.lower()}_attribute': (
                                        inserted_value if isinstance(inserted_value, bool)
                                        else str(inserted_value))}]))
    assert REST_response.status_code == 200
    REST_records = client.get(f'/schema/{table.database}/table/{table.__name__}/record',
                              headers=dict(Authorization=f'Bearer {token}')
                              ).json['records']
    assert len(REST_records) == 1
    assert isinstance(REST_records[0][1], expected_type) and \
        REST_records[0][1] == expected_value


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
    ScanData, ProcessScanData = ParentPart
    ScanData.insert1(dict(scan_id=0, data=5))
    ProcessScanData.populate()

    # Test Parent
    REST_value = client.get(
        f'/schema/{ScanData.database}/table/{ProcessScanData.__name__}/record',
        headers=dict(Authorization=f'Bearer {token}')).json['records'][0]

    assert REST_value == [0, 5]

    # Test Child
    REST_value = client.get(
        f"""/schema/{ProcessScanData.database}/table/{
            ProcessScanData.__name__ + '.' +
            ProcessScanData.ProcessScanDataPart.__name__}/record""",
        headers=dict(Authorization=f'Bearer {token}')).json['records'][0]

    assert REST_value == [0, 10]
