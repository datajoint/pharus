

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
    schema = dj.Schema('schema', connection=connection)
    yield schema
    schema.drop()
    
@pytest.fixture
def test_list_tables(schema, client, token):
    # Create example table
    class TestTable(dj.Manual):
        definition="""
        test_id: int
        """

    # Testing for schema that exists
    client.post(
        '/api/list_tables', 
        json=dict(schema_name='schema_test',
        headers=dict(Authorization=f'Bearer {token}')
        ))