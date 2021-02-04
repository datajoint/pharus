"""Library for interfaces into DataJoint pipelines."""
import datajoint as dj
from datajoint.declare import TYPE_PATTERN
import datetime
import numpy as np
from decimal import Decimal

DAY = 24 * 60 * 60

class DJConnector():
    """
    Primary connector that communicates with a DataJoint database server.
    """
    @staticmethod
    def attempt_login(database_address: str, username: str, password: str):
        """
        Attempts to authenticate against database with given username and address
        :param database_address: Address of database
        :type database_address: str
        :param username: Username of user
        :type username: str
        :param password: Password of user
        :type password: str
        :return: Dictionary with keys: result(True|False), and error (if applicable)
        :rtype: dict
        """
        dj.config['database.host'] = database_address
        dj.config['database.user'] = username
        dj.config['database.password'] = password

        # Attempt to connect return true if successful, false is failed
        try:
            dj.conn(reset=True)
            return dict(result=True)
        except Exception as e:
            return dict(result=False, error=e)

    @staticmethod
    def list_schemas(jwt_payload: dict):
        """
        List all schemas under the database
        :param jwt_payload: Dictionary containing databaseAddress, username and password
            strings
        :type jwt_payload: dict
        :return: List of schemas names in alphabetical order excluding information_schema
        :rtype: list
        """
        DJConnector.set_datajoint_config(jwt_payload)

        # Attempt to connect return true if successful, false is failed
        return [row[0] for row in dj.conn().query("""
        SELECT SCHEMA_NAME FROM information_schema.schemata
        WHERE SCHEMA_NAME != "information_schema"
        ORDER BY SCHEMA_NAME
        """)]

    @staticmethod
    def list_tables(jwt_payload: dict, schema_name: str):
        """
        List all tables and their type give a schema
        :param jwt_payload: Dictionary containing databaseAddress, username and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema to list all tables from
        :type schema_name: str
        :return: Contains a key for a each table type and it corressponding table names
        :rtype: dict
        """
        DJConnector.set_datajoint_config(jwt_payload)

        # Get list of tables names\
        tables_name = dj.schema(schema_name).list_tables()

        # Dict to store list of table name for each type
        tables_dict_list = dict(manual_tables=[], lookup_tables=[], computed_tables=[],
                                imported_tables=[], part_tables=[])

        # Loop through each table name to figure out what type it is and add them to
        # tables_dict_list
        for table_name in tables_name:
            table_type = dj.diagram._get_tier(
                '`' + schema_name + '`.`' + table_name + '`').__name__
            print(table_name, table_type, flush=True)
            if table_type == 'Manual':
                tables_dict_list['manual_tables'].append(dj.utils.to_camel_case(table_name))
            elif table_type == 'Lookup':
                tables_dict_list['lookup_tables'].append(dj.utils.to_camel_case(table_name))
            elif table_type == 'Computed':
                tables_dict_list['computed_tables'].append(dj.utils.to_camel_case(table_name))
            elif table_type == 'Imported':
                tables_dict_list['imported_tables'].append(dj.utils.to_camel_case(table_name))
            elif table_type == 'Part':
                table_name_parts = table_name.split('__')
                tables_dict_list['part_tables'].append(DJConnector.snake_to_camel_case(
                    table_name_parts[-2]) + '.' + DJConnector.snake_to_camel_case(
                        table_name_parts[-1]))
            else:
                print(table_name + ' is of unknown table type')

        return tables_dict_list

    @staticmethod
    def fetch_tuples(jwt_payload: dict, schema_name: str, table_name: str):
        """
        Get records as tuples from table
        :param jwt_payload: Dictionary containing databaseAddress, username and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema to list all tables from
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :return: List of tuples in dict form
        :rtype: list
        """
        DJConnector.set_datajoint_config(jwt_payload)

        schema_virtual_module = dj.create_virtual_module(schema_name, schema_name)

        # Get the table object refernece
        table = getattr(schema_virtual_module, table_name)
        
        # Fetch tuples without blobs as dict to be used to create a 
        #   list of tuples for returning
        tuples_without_blobs = table.fetch(*table.heading.non_blobs, as_dict=True)

        # Buffer list to be return
        tuples = []

        # Looped through each tuple and deal with TEMPORAL types and replacing 
        #   blobs with ==BLOB== for json encoding
        for tuple_without_blob in tuples_without_blobs:
            tuple_buffer = []
            for attribute_name, attribute_info in table.heading.attributes.items():
                if not attribute_info.is_blob:
                    if tuple_without_blob[attribute_name] == None:
                        # If it is none then just append None
                        tuple_buffer.append(None)
                    elif attribute_info.type == 'date':
                        # Date attribute type covert to epoch time
                        tuple_buffer.append((tuple_without_blob[attribute_name] - datetime.date(1970, 1, 1)).days * DAY)
                    elif attribute_info.type == 'time':
                        # Time attirbute, return total seconds
                        tuple_buffer.append(tuple_without_blob[attribute_name].total_seconds())
                    elif attribute_info.type in ('datetime', 'timestamp'):
                        # Datetime or timestamp, use timestamp to covert to epoch time
                        tuple_buffer.append(tuple_without_blob[attribute_name].timestamp())
                    elif attribute_info.type[0:7] == 'decimal':
                        # Covert decimal to string
                        tuple_buffer.append(str(tuple_without_blob[attribute_name]))
                    else:
                        # Normal attribute, just return value with .item to deal with numpy types
                        if type(tuple_without_blob[attribute_name]).__module__ == np.__name__:
                            tuple_buffer.append(tuple_without_blob[attribute_name].item())
                        else:
                            tuple_buffer.append(tuple_without_blob[attribute_name])
                else:
                    # Attribute is blob type thus fill it in string instead
                    tuple_buffer.append('=BLOB=')
            tuples.append(tuple_buffer)
        return tuples

    @staticmethod
    def get_table_attributes(jwt_payload: dict, schema_name: str, table_name: str):
        """
        Method to get primary and secondary attributes of a table
        :param jwt_payload: Dictionary containing databaseAddress, username and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema to list all tables from
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :return: Dict of primary, secondary attributes and with metadata: attribute_name,
            type, nullable, default, autoincrement.
        :rtype: dict
        """
        DJConnector.set_datajoint_config(jwt_payload)

        schema_virtual_module = dj.create_virtual_module(schema_name, schema_name)
        table_attributes = dict(primary_attributes=[], secondary_attributes=[])
        for attribute_name, attribute_info in getattr(schema_virtual_module,
                                                      table_name).heading.attributes.items():
            if attribute_info.in_key:
                table_attributes['primary_attributes'].append((
                    attribute_name,
                    attribute_info.type,
                    attribute_info.nullable,
                    attribute_info.default,
                    attribute_info.autoincrement
                    ))
            else:
                table_attributes['secondary_attributes'].append((
                    attribute_name,
                    attribute_info.type,
                    attribute_info.nullable,
                    attribute_info.default,
                    attribute_info.autoincrement
                    ))

        return table_attributes

    @staticmethod
    def get_table_definition(jwt_payload: dict, schema_name: str, table_name: str):
        """
        Get the table definition
        :param jwt_payload: Dictionary containing databaseAddress, username and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema to list all tables from
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :return: definition of the table
        :rtype: str
        """
        DJConnector.set_datajoint_config(jwt_payload)

        schema_virtual_module = dj.create_virtual_module(schema_name, schema_name)
        return getattr(schema_virtual_module, table_name).describe()

    @staticmethod
    def insert_tuple(jwt_payload: dict, schema_name: str, table_name: str,
                     tuple_to_insert: dict):
        """
        Insert record as tuple into table
        :param jwt_payload: Dictionary containing databaseAddress, username and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema to list all tables from
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :param tuple_to_insert: Record to be inserted
        :type tuple_to_insert: dict
        """
        DJConnector.set_datajoint_config(jwt_payload)

        schema_virtual_module = dj.create_virtual_module(schema_name, schema_name)
        getattr(schema_virtual_module, table_name).insert1(tuple_to_insert)

    @staticmethod
    def update_tuple(jwt_payload: dict, schema_name: str, table_name: str,
                     tuple_to_update: dict):
        """
        Update record as tuple into table
        :param jwt_payload: Dictionary containing databaseAddress, username and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema to list all tables from
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :param tuple_to_update: Record to be updated
        :type tuple_to_update: dict
        """
        DJConnector.set_datajoint_config(jwt_payload)

        schema_virtual_module = dj.create_virtual_module(schema_name, schema_name)
        getattr(schema_virtual_module, table_name).update1(tuple_to_update)

    @staticmethod
    def delete_tuple(jwt_payload: dict, schema_name: str, table_name: str,
                     tuple_to_restrict_by: dict):
        """
        Delete a specific record based on the restriction given (Can only delete 1 at a time)
        :param jwt_payload: Dictionary containing databaseAddress, username and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema to list all tables from
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :param tuple_to_restrict_by: Record to restrict the table by to delete
        :type tuple_to_restrict_by: dict
        """
        DJConnector.set_datajoint_config(jwt_payload)

        schema_virtual_module = dj.create_virtual_module(schema_name, schema_name)
        # Get all the table attributes and create a set
        table_attributes = set(getattr(schema_virtual_module,
                                       table_name).heading.primary_key +
                               getattr(schema_virtual_module,
                                       table_name).heading.secondary_attributes)

        # Check to see if the restriction has at least one matching attribute, if not raise an
        # error
        if len(table_attributes & tuple_to_restrict_by.keys()) == 0:
            raise Exception('Restriction is invalid: None of the attributes match')

        # Compute restriction
        tuple_to_delete = getattr(schema_virtual_module, table_name) & tuple_to_restrict_by

        # Check if there is only 1 tuple to delete otherwise raise error
        if len(tuple_to_delete) > 1:
            raise Exception("""Cannot delete more than 1 tuple at a time.
                            Please update the restriction accordingly""")
        elif len(tuple_to_delete) == 0:
            raise Exception('Nothing to delete')

        # All check pass thus proceed to delete
        tuple_to_delete.delete_quick()

    @staticmethod
    def set_datajoint_config(jwt_payload: dict):
        """
        Method to set credentials for database
        :param jwt_payload: Dictionary containing databaseAddress, username and password
            strings
        :type jwt_payload: dict
        """
        dj.config['database.host'] = jwt_payload['databaseAddress']
        dj.config['database.user'] = jwt_payload['username']
        dj.config['database.password'] = jwt_payload['password']

        dj.conn(reset=True)

    @staticmethod
    def snake_to_camel_case(string: str):
        """
        Helper method for converting snake to camel case
        :param string: String in snake format to convert to camel case
        :type string: str
        :return: String formated in CamelCase notation
        :rtype: str
        """
        return ''.join(string_component.title() for string_component in string.split('_'))
