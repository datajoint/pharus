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
        jwt_payload (dict): Dictionary containing databaseAddress, username and password strings

    Returns:
        list<strings>: List of schemas names in alphabetical order excluding information_schema
    """
    @staticmethod
    def list_schemas(jwt_payload):
        DJConnector.set_datajoint_config(jwt_payload)

        # Attempt to connect return true if successful, false is failed
        return [row[0] for row in dj.conn().query('SELECT SCHEMA_NAME FROM information_schema.schemata WHERE SCHEMA_NAME != "information_schema" ORDER BY SCHEMA_NAME')]

    """
    List all tables and their type give a schema

    Parameters:
        jwt_payload (dict): Dictionary containing databaseAddress, username and password strings
        schema_name (str): Name of schema to list all tables from

    Returns:
        dict(manual_tables=[<table_names>], 
            lookup_tables=[<table_names>], 
            computed_tables=[<computed_tables>], 
            part_tables=[<table_names>]
            ): dict containg a key for a each table type and it corressponding table names
    """
    @staticmethod
    def list_tables(jwt_payload, schema_name):
        DJConnector.set_datajoint_config(jwt_payload)
        
        # Get list of tables names\
        tables_name = dj.schema(schema_name).list_tables()

        # Dict to store list of table name for each type
        tables_dict_list = dict(manual_tables=[], lookup_tables=[], computed_tables=[], part_tables=[])

        # Loop through each table name to figure out what type it is and add them to tables_dict_list
        for table_name in tables_name:
            table_type = dj.diagram._get_tier('`' + schema_name + '`.`' + table_name + '`').__name__
            
            if table_type == 'Manual':
                tables_dict_list['manual_tables'].append(dj.utils.to_camel_case(table_name))
            elif table_type == 'Lookup':
                tables_dict_list['lookup_tables'].append(dj.utils.to_camel_case(table_name))
            elif table_type == 'Computed':
                tables_dict_list['computed_tables'].append(dj.utils.to_camel_case(table_name))
            elif table_type == 'Part':
                table_name_parts = table_name.split('__')
                tables_dict_list['part_tables'].append(DJConnector.snake_to_camel_case(table_name_parts[1]) + '.' + DJConnector.snake_to_camel_case(table_name_parts[2]))
            else:
                print(table_name + ' is of unknown table type')

        return tables_dict_list

    """
    Get all tuples from table
    
    Parameters:
        jwt_payload (dict): Dictionary containing databaseAddress, username and password strings
        schema_name (string): Schema name where to find the table under
        table_name (string): Table name under the given schema, must be in camel case

    Returns:
        list<tuples_as_dicts>: a list of tuples in dict form
    """
    @staticmethod
    def fetch_tuples(jwt_payload, schema_name, table_name):
        DJConnector.set_datajoint_config(jwt_payload)
        
        schema_virtual_module = dj.create_virtual_module(schema_name, schema_name)
        return getattr(schema_virtual_module, table_name).fetch(as_dict=True)

    """
    Method to get primary and secondary attributes of a table

    Parameters:
        jwt_payload (dict): Dictionary containing databaseAddress, username and password strings
        schema_name (string): Schema name where to find the table under
        table_name (string): Table name under the given schema, must be in camel case

    Returns:
        dict(primary_keys=[<primary_key_names>], secondary_attributes=[<secondary_key_names])
    """
    @staticmethod
    def get_table_attributes(jwt_payload, schema_name, table_name):
        DJConnector.set_datajoint_config(jwt_payload)

        schema_virtual_module = dj.create_virtual_module(schema_name, schema_name)
        return dict(primary_keys=getattr(schema_virtual_module, table_name).heading.primary_key, secondary_attributes=getattr(schema_virtual_module, table_name).heading.secondary_attributes)
        
    """
    Get the table definition

    Parameters:
        jwt_payload (dict): Dictionary containing databaseAddress, username and password strings
        schema_name (string): Schema name where to find the table under
        table_name (string): Table name under the given schema, must be in camel case

    Returns:
        string: definition of the table
    """
    @staticmethod
    def get_table_definition(jwt_payload, schema_name, table_name):
        DJConnector.set_datajoint_config(jwt_payload)
        
        schema_virtual_module = dj.create_virtual_module(schema_name, schema_name)
        return getattr(schema_virtual_module, table_name).describe()

    """
    Insert tuple table

    Parameters:
        jwt_payload (dict): Dictionary containing databaseAddress, username and password strings
        schema_name (string): Schema name where to find the table under
        table_name (string): Table name under the given schema, must be in camel case
        tuple (dict): tuple to be inserted

    Returns:
        None
    """
    @staticmethod
    def insert_tuple(jwt_payload, schema_name, table_name, tuple_to_insert):
        DJConnector.set_datajoint_config(jwt_payload)
        
        schema_virtual_module = dj.create_virtual_module(schema_name, schema_name)
        getattr(schema_virtual_module, table_name).insert1(tuple_to_insert)

    """
    Delete a specific tuple based on the restriction given (Can only delete 1 at a time)

    Parameters:
        jwt_payload (dict): Dictionary containing databaseAddress, username and password strings
        schema_name (string): Schema name where to find the table under
        table_name (string): Table name under the given schema, must be in camel case
        tuple_to_restrict_by (dict): tuple to restrict the table by to delete
    
    Returns:
        None: (Assuming it was valid, otherwise it will raise an error)
    """
    @staticmethod
    def delete_tuple(jwt_payload, schema_name, table_name, tuple_to_restrict_by):
        DJConnector.set_datajoint_config(jwt_payload)

        schema_virtual_module = dj.create_virtual_module(schema_name, schema_name)
        # Get all the table attributes and create a set
        table_attributes = set(getattr(schema_virtual_module, table_name).heading.primary_key + getattr(schema_virtual_module, table_name).heading.secondary_attributes)

        # Check to see if the restriction has at least one matching attribute, if not raise an error
        if len(table_attributes & tuple_to_restrict_by.keys()) == 0:
            raise Exception('Restriction is invalid: None of the attributes match')

        # Compute restriction 
        tuple_to_delete = getattr(schema_virtual_module, table_name) & tuple_to_restrict_by

        # Check if there is only 1 tuple to delete otherwise raise error
        
        if len(tuple_to_delete) > 1:
            raise Exception('Cannot delete more than 1 tuple at a time. Please update the restriction accordingly')
        elif len(tuple_to_delete) == 0:
            raise Exception('Nothing to delete')

        # All check pass thus proceed to delete
        tuple_to_delete.delete_quick()
        
    """
    Method to set credentials for database
    
    Parameters:
        jwt_payload (dict): dictionary containing databaseAddress, username and password strings

    Returns:
        None
    """
    @staticmethod
    def set_datajoint_config(jwt_payload):
        dj.config['database.host'] = jwt_payload['databaseAddress']
        dj.config['database.user'] = jwt_payload['username']
        dj.config['database.password'] = jwt_payload['password']
    
        dj.conn(reset=True)

    """
    Helper method for converting snake to camel case

    Parameters:
        string (string): String in snake format to convert to camel case

    Returns:
        string: String formated in CamelCase notation
    """
    @staticmethod
    def snake_to_camel_case(string):
        return ''.join(string_component.title() for string_component in string.split('_'))