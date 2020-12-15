import datajoint as dj

class DJConnector():
    """
    Attempt to authenticate against database with given username and address

    Parameters:
        database_address (string): Address of database
        username (string): Username of user
        password (string): Password of user

    Returns:
        dict(result=True): If successful
        dict(result=False, error=<error-message>): If failed
    """
    @staticmethod
    def attempt_login(database_address, username, password):
        dj.config['database.host'] = database_address
        dj.config['database.user'] = username
        dj.config['database.password'] = password
        
        # Attempt to connect return true if successful, false is failed
        try:
            dj.conn(reset=True)
            return dict(result=True)
        except Exception as e:
            return dict(result=False, error=e)

    """
    List all schemas under the database

    Parameters:
        database_address (string): Address of database
        username (string): Username of user
        password (string): Password of user

    Returns:
        dict(result=True, schemas=(list(str))): If successful
        dict(result=False, error=<error-message>): If failed
    """
    @staticmethod
    def list_schemas(database_address, username, password):
        dj.config['database.host'] = database_address
        dj.config['database.user'] = username
        dj.config['database.password'] = password

        # Attempt to connect return true if successful, false is failed
        try:
            schemas = dj.list_schemas()
            return dict(result=True, schemas=schemas)
        except Exception as e:
            return dict(result=False, error=e)