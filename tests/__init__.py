import pytest
from pharus.dynamic_api import app
from uuid import UUID
from os import getenv
import datajoint as dj
from datetime import date
from random import randint, choice, seed, getrandbits
from faker import Faker

seed("lock")  # Pin down randomizer between runs
faker = Faker()
Faker.seed(0)  # Pin down randomizer between runs
SCHEMA_PREFIX = "test_"


@pytest.fixture
def client():
    """REST client interface."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def token(client):
    """Root Bearer token."""
    yield client.post(
        "/login",
        json=dict(
            databaseAddress=getenv("TEST_DB_SERVER"),
            username=getenv("TEST_DB_USER"),
            password=getenv("TEST_DB_PASS"),
        ),
    ).json["jwt"]


@pytest.fixture
def group1_token(client, connection):
    connection.query(
        """
        CREATE USER IF NOT EXISTS 'group1'@'%%'
        IDENTIFIED BY 'group1';
        """
    )
    connection.query(
        f"GRANT ALL PRIVILEGES ON `{SCHEMA_PREFIX}group1_%%`.* TO 'group1'@'%%';"
    )
    yield client.post(
        "/login",
        json=dict(
            databaseAddress=getenv("TEST_DB_SERVER"),
            username="group1",
            password="group1",
        ),
    ).json["jwt"]
    connection.query("DROP USER 'group1'@'%%';")


@pytest.fixture
def connection():
    """Root database connection."""
    dj.config["safemode"] = False
    connection = dj.Connection(
        host=getenv("TEST_DB_SERVER"),
        user=getenv("TEST_DB_USER"),
        password=getenv("TEST_DB_PASS"),
    )
    yield connection
    dj.config["safemode"] = True
    connection.close()


@pytest.fixture
def schema_main(connection):
    """Main test schema."""
    main = dj.Schema(f"{SCHEMA_PREFIX}main", connection=connection)
    yield main
    main.drop()


@pytest.fixture
def schemas_simple(connection):
    """Simple test schemas."""

    group1_simple = dj.Schema(f"{SCHEMA_PREFIX}group1_simple", connection=connection)
    group2_simple = dj.Schema(f"{SCHEMA_PREFIX}group2_simple", connection=connection)
    group3_simple = dj.Schema(f"{SCHEMA_PREFIX}group3_simple", connection=connection)
    group4_simple = dj.Schema(f"{SCHEMA_PREFIX}group4_simple", connection=connection)

    @group1_simple
    class TableA(dj.Lookup):
        definition = """
        a_id: int
        ---
        a_name: varchar(30)
        """
        contents = [
            (
                0,
                "Raphael",
            ),
            (
                1,
                "Bernie",
            ),
        ]

    @group1_simple
    class TableB(dj.Lookup):
        definition = """
        -> TableA
        b_id: int
        ---
        b_number: float
        """
        contents = [
            (0, 10, 22.12),
            (
                0,
                11,
                -1.21,
            ),
            (
                1,
                21,
                7.77,
            ),
        ]

    @group2_simple
    class DiffTableB(dj.Lookup):
        definition = """
        -> TableA
        bs_id: int
        ---
        bs_number: float
        """
        contents = [
            (0, -10, -99.99),
            (
                0,
                -11,
                287.11,
            ),
        ]

    @group1_simple
    class TableC(dj.Lookup):
        definition = """
        -> TableB
        c_id: int
        ---
        c_int: int
        """
        contents = [
            (0, 10, 100, -8),
            (
                0,
                11,
                200,
                -9,
            ),
            (
                0,
                11,
                300,
                -7,
            ),
        ]

    @group3_simple
    class TableZ(dj.Lookup):
        definition = """
        z_id: int
        ---
        z_name: varchar(30)
        """
        contents = [
            (
                0,
                "Adib",
            ),
            (
                1,
                "Bert",
            ),
        ]

    @group4_simple
    class DiffTableZ(dj.Lookup):
        definition = """
        zs_id: int
        ---
        zs_name: varchar(30)
        """
        contents = [
            (
                0,
                "Jeroen",
            ),
            (
                1,
                "Elmo",
            ),
        ]

    @group3_simple
    class TableY(dj.Lookup):
        definition = """
        -> DiffTableZ
        y_id: int
        ---
        y_number: float
        """
        contents = [
            (0, 21, 33.23),
            (
                0,
                22,
                -2.32,
            ),
            (
                1,
                32,
                8.88,
            ),
        ]

    @group4_simple
    class DiffTableY(dj.Lookup):
        definition = """
        -> TableZ
        ys_id: int
        ---
        ys_number: float
        """
        contents = [
            (0, 32, 44.34),
            (
                0,
                33,
                -3.43,
            ),
            (
                1,
                43,
                9.99,
            ),
        ]

    @group3_simple
    class TableX(dj.Lookup):
        definition = """
        x_id: int
        x_name: varchar(30)
        x_int: int
        """
        contents = [
            (
                0,
                "Carlos",
                10,
            ),
            (
                1,
                "Oscar",
                20,
            ),
        ]

    @group4_simple
    class TableW(dj.Lookup):
        definition = """
        -> TableX
        w_id: int
        ---
        w_int: int
        """

    @group1_simple
    class PlotlyTable(dj.Lookup):
        definition = """
        p_id: int
        ---
        plot: longblob
        """
        contents = [
            (
                2,
                dict(
                    data=[
                        dict(
                            x=[1, 2, 3],
                            y=[2, 6, 3],
                            type="scatter",
                            mode="lines+markers",
                            marker=dict(color="red"),
                        ),
                        dict(type="bar", x=[1, 2, 3], y=[2, 5, 3]),
                    ],
                    layout=dict(title="A Fancy Plot"),
                ),
            )
        ]

    yield group1_simple, group2_simple

    group2_simple.drop()
    group1_simple.drop()


@pytest.fixture
def Student(schema_main):
    """Student table for testing."""

    @schema_main
    class Student(dj.Lookup):
        definition = """
        student_id: int
        ---
        student_name: varchar(50)
        student_ssn: varchar(20)
        student_enroll_date: datetime
        student_balance: float
        student_parking_lot=null : varchar(20)
        student_out_of_state: bool
        """
        contents = [
            (
                i,
                faker.name(),
                faker.ssn(),
                faker.date_between_dates(
                    date_start=date(2021, 1, 1), date_end=date(2021, 1, 31)
                ),
                round(randint(1000, 3000), 2),
                choice([None, "LotA", "LotB", "LotC"]),
                bool(getrandbits(1)),
            )
            for i in range(100)
        ]

    yield Student
    Student.drop()


@pytest.fixture
def Computer(schema_main):
    """Computer table for testing."""

    @schema_main
    class Computer(dj.Lookup):
        definition = """
        computer_id: uuid
        ---
        computer_brand: enum('HP', 'DELL')
        """
        contents = [
            (UUID("ffffffff-86d5-4af7-a013-89bde75528bd"), "HP"),
            (UUID("aaaaaaaa-86d5-4af7-a013-89bde75528bd"), "DELL"),
        ]

    yield Computer
    Computer.drop()


@pytest.fixture
def Int(schema_main):
    """Integer basic table for testing."""

    @schema_main
    class Int(dj.Manual):
        definition = """
        id: int
        ---
        int_attribute: int
        """

    yield Int
    Int.drop()


@pytest.fixture
def Float(schema_main):
    """Float basic table for testing."""

    @schema_main
    class Float(dj.Manual):
        definition = """
        id: int
        ---
        float_attribute: float
        """

    yield Float
    Float.drop()


@pytest.fixture
def Decimal(schema_main):
    """Decimal basic table for testing."""

    @schema_main
    class Decimal(dj.Manual):
        definition = """
        id: int
        ---
        decimal_attribute: decimal(5, 2)
        """

    yield Decimal
    Decimal.drop()


@pytest.fixture
def String(schema_main):
    @schema_main
    class String(dj.Manual):
        definition = """
        id: int
        ---
        string_attribute: varchar(32)
        """

    yield String
    String.drop()


@pytest.fixture
def Bool(schema_main):
    @schema_main
    class Bool(dj.Manual):
        definition = """
        id: int
        ---
        bool_attribute: bool
        """

    yield Bool
    Bool.drop()


@pytest.fixture
def Date(schema_main):
    @schema_main
    class Date(dj.Manual):
        definition = """
        id: int
        ---
        date_attribute: date
        """

    yield Date
    Date.drop()


@pytest.fixture
def Datetime(schema_main):
    @schema_main
    class Datetime(dj.Manual):
        definition = """
        id: int
        ---
        datetime_attribute: datetime
        """

    yield Datetime
    Datetime.drop()


@pytest.fixture
def Timestamp(schema_main):
    @schema_main
    class Timestamp(dj.Manual):
        definition = """
        id: int
        ---
        timestamp_attribute: timestamp
        """

    yield Timestamp
    Timestamp.drop()


@pytest.fixture
def Time(schema_main):
    @schema_main
    class Time(dj.Manual):
        definition = """
        id: int
        ---
        time_attribute: time
        """

    yield Time
    Time.drop()


@pytest.fixture
def Blob(schema_main):
    @schema_main
    class Blob(dj.Manual):
        definition = """
        id: int
        ---
        blob_attribute: blob
        """

    yield Blob
    Blob.drop()


@pytest.fixture
def Longblob(schema_main):
    @schema_main
    class Longblob(dj.Manual):
        definition = """
        id: int
        ---
        longblob_attribute: longblob
        """

    yield Longblob
    Longblob.drop()


@pytest.fixture
def Uuid(schema_main):
    @schema_main
    class Uuid(dj.Manual):
        definition = """
        id: int
        ---
        uuid_attribute: uuid
        """

    yield Uuid
    Uuid.drop()


@pytest.fixture
def ParentPart(schema_main):
    @schema_main
    class ScanData(dj.Manual):
        definition = """
        scan_id : int unsigned
        ---
        data: int unsigned
        """

    @schema_main
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
            self.insert1(dict(key, processed_scan_data=scan_data_dict["data"]))
            self.ProcessScanDataPart.insert1(
                dict(key, processed_scan_data_part=scan_data_dict["data"] * 2)
            )

    yield ScanData, ProcessScanData
    ScanData.drop()
