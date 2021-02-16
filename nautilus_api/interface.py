"""Library for interfaces into DataJoint pipelines."""
import datajoint as dj
import datetime
import numpy as np
from functools import reduce
from datajoint.errors import AccessError
import re
from .error import InvalidDeleteRequest, InvalidRestriction, UnsupportedTableType

DAY = 24 * 60 * 60
DEFAULT_FETCH_LIMIT = 1000  # Stop gap measure to deal with super large tables
TABLE_INFO_REGEX = re.compile(
    r'.*?FROM\s+`(?P<schema>\w+)`.*?name\s*?=\s*?"(?P<table>.*?)".*?')


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
        dj.conn(reset=True)
        return dict(result=True)

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
        WHERE SCHEMA_NAME NOT IN ("information_schema", "sys", "performance_schema", "mysql")
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
                raise UnsupportedTableType(table_name + ' is of unknown table type')

        return tables_dict_list

    @staticmethod
    def fetch_tuples(jwt_payload: dict, schema_name: str, table_name: str,
                     restriction: list = [], limit: int = 1000, page: int = 1,
                     order=['KEY ASC']) -> tuple:
        """
        Get records as tuples from table
        :param jwt_payload: Dictionary containing databaseAddress, username and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema to list all tables from
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :param restriction: Sequence of filter cards with attribute_name, operation, value
            defined, defaults to []
        :type restriction: list, optional
        :param limit: Max number of records to return, defaults to 1000
        :type limit: int, optional
        :param page: Page number to return, defaults to 1
        :type page: int, optional
        :param order: Sequence to order records, defaults to ['KEY ASC'].
            See :class:`datajoint.fetch.Fetch` for more info.
        :type order: list, optional
        :return: Records in dict form and the total number of records that can be paged
        :rtype: tuple
        """
        def filter_to_restriction(attribute_filter: dict) -> str:
            if attribute_filter['operation'] in ('>', '<', '>=', '<='):
                operation = attribute_filter['operation']
            elif attribute_filter['value'] is None:
                operation = (' IS ' if attribute_filter['operation'] == '='
                             else ' IS NOT ')
            else:
                operation = attribute_filter['operation']

            if (isinstance(attribute_filter['value'], str) and
                    not attribute_filter['value'].isnumeric()):
                value = f"'{attribute_filter['value']}'"
            else:
                value = ('NULL' if attribute_filter['value'] is None
                         else attribute_filter['value'])

            return f"{attribute_filter['attributeName']}{operation}{value}"

        DJConnector.set_datajoint_config(jwt_payload)

        schema_virtual_module = dj.create_virtual_module(schema_name, schema_name)

        # Get table object from name
        table = DJConnector.get_table_object(schema_virtual_module, table_name)

        # Fetch tuples without blobs as dict to be used to create a
        #   list of tuples for returning
        query = reduce(lambda q1, q2: q1 & q2, [table()] + [filter_to_restriction(f)
                                                            for f in restriction])
        non_blobs_rows = query.fetch(*table.heading.non_blobs, as_dict=True, limit=limit,
                                     offset=(page-1)*limit, order_by=order)

        # Buffer list to be return
        rows = []

        # Looped through each tuple and deal with TEMPORAL types and replacing
        #   blobs with ==BLOB== for json encoding
        for non_blobs_row in non_blobs_rows:
            # Buffer object to store the attributes
            row = []
            # Loop through each attributes, append to the tuple_to_return with specific
            #   modification based on data type
            for attribute_name, attribute_info in table.heading.attributes.items():
                if not attribute_info.is_blob:
                    if non_blobs_row[attribute_name] is None:
                        # If it is none then just append None
                        row.append(None)
                    elif attribute_info.type == 'date':
                        # Date attribute type covert to epoch time
                        row.append((non_blobs_row[attribute_name] -
                                    datetime.date(1970, 1, 1)).days * DAY)
                    elif attribute_info.type == 'time':
                        # Time attirbute, return total seconds
                        row.append(non_blobs_row[attribute_name].total_seconds())
                    elif attribute_info.type in ('datetime', 'timestamp'):
                        # Datetime or timestamp, use timestamp to covert to epoch time
                        row.append(non_blobs_row[attribute_name].timestamp())
                    elif attribute_info.type[0:7] == 'decimal':
                        # Covert decimal to string
                        row.append(str(non_blobs_row[attribute_name]))
                    else:
                        # Normal attribute, just return value with .item to deal with numpy
                        #   types
                        if isinstance(non_blobs_row[attribute_name], np.generic):
                            row.append(np.asscalar(non_blobs_row[attribute_name]))
                        else:
                            row.append(non_blobs_row[attribute_name])
                else:
                    # Attribute is blob type thus fill it in string instead
                    row.append('=BLOB=')

            # Add the row list to tuples
            rows.append(row)
        return rows, len(query)

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

        # Get table object from name
        table = DJConnector.get_table_object(schema_virtual_module, table_name)

        table_attributes = dict(primary_attributes=[], secondary_attributes=[])
        for attribute_name, attribute_info in table.heading.attributes.items():
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
    def record_dependency(jwt_payload: dict, schema_name: str, table_name: str,
                          primary_restriction: dict) -> list:
        """
        Return summary of dependencies associated with a restricted table
        :param jwt_payload: Dictionary containing databaseAddress, username and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :param primary_restriction: Restriction to be applied to table
        :type primary_restriction: dict
        :return: Tables that are dependant on specific records. Includes accessibility and,
            if accessible, how many rows are affected.
        :rtype: list
        """
        DJConnector.set_datajoint_config(jwt_payload)
        virtual_module = dj.VirtualModule(schema_name, schema_name)
        table = getattr(virtual_module, table_name)
        # Retrieve dependencies of related to retricted
        dependencies = [dict(schema=descendant.database, table=descendant.table_name,
                             accessible=True, count=len(descendant & primary_restriction))
                        for descendant in table().descendants(as_objects=True)]
        # Determine first issue regarding access
        # Start transaction, try to delete, catch first occurrence, rollback
        virtual_module.schema.connection.start_transaction()
        try:
            (table & primary_restriction).delete(safemode=False, transaction=False)
        except AccessError as errors:
            dependencies = dependencies + [dict(TABLE_INFO_REGEX.match(
                errors.args[2]).groupdict(), accessible=False)]
        finally:
            virtual_module.schema.connection.cancel_transaction()
        return dependencies

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
            raise InvalidRestriction('Restriction is invalid: None of the attributes match')

        # Compute restriction
        tuple_to_delete = getattr(schema_virtual_module, table_name) & tuple_to_restrict_by

        # Check if there is only 1 tuple to delete otherwise raise error
        if len(tuple_to_delete) > 1:
            raise InvalidDeleteRequest("""Cannot delete more than 1 tuple at a time.
                            Please update the restriction accordingly""")
        elif len(tuple_to_delete) == 0:
            raise InvalidDeleteRequest('Nothing to delete')

        # All check pass thus proceed to delete
        tuple_to_delete.delete(safemode=False)

    @staticmethod
    def get_table_object(schema_virtual_module, table_name: str):
        """
        Helper method for getting the table object based on the table_name provided
        :param schema_virtual_module: dj.VirtualModule for accesing the schema
        :type schema_virtual_module: dj.VirtualModule
        :param table_name: name of the table, for part it should be parent.part
        :type table_name: str
        """
        # Split the table name by '.' for dealing with part tables
        table_name_parts = table_name.split('.')
        if len(table_name_parts) == 2:
            return getattr(getattr(schema_virtual_module, table_name_parts[0]),
                           table_name_parts[1])
        else:
            return getattr(schema_virtual_module, table_name_parts[0])

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
