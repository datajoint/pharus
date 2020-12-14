import datajoint as dj

class DJConnector():
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