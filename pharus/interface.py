"""Library for interfaces into DataJoint pipelines."""
import datajoint as dj
from datajoint.utils import to_camel_case
from datajoint.user_tables import UserTable
from datajoint import VirtualModule
import datetime
import numpy as np
from .error import InvalidRestriction, UnsupportedTableType

DAY = 24 * 60 * 60
DEFAULT_FETCH_LIMIT = 1000  # Stop gap measure to deal with super large tables


class _DJConnector():
    """Primary connector that communicates with a DataJoint database server."""

    @staticmethod
    def _attempt_login(database_address: str, username: str, password: str):
        """
        Attempts to authenticate against database with given username and address.

        :param database_address: Address of database
        :type database_address: str
        :param username: Username of user
        :type username: str
        :param password: Password of user
        :type password: str
        """
        dj.config['database.host'] = database_address
        dj.config['database.user'] = username
        dj.config['database.password'] = password

        # Attempt to connect return true if successful, false is failed
        dj.conn(reset=True)

    @staticmethod
    def _list_schemas(jwt_payload: dict) -> list:
        """
        List all schemas under the database.

        :param jwt_payload: Dictionary containing databaseAddress, username, and password
            strings
        :type jwt_payload: dict
        :return: List of schemas names in alphabetical order (excludes ``information_schema``,
            ``sys``, ``performance_schema``, ``mysql``)
        :rtype: list
        """
        _DJConnector._set_datajoint_config(jwt_payload)

        # Attempt to connect return true if successful, false is failed
        return [row[0] for row in dj.conn().query("""
        SELECT SCHEMA_NAME FROM information_schema.schemata
        WHERE SCHEMA_NAME NOT IN ("information_schema", "sys", "performance_schema", "mysql")
        ORDER BY SCHEMA_NAME
        """)]

    @staticmethod
    def _list_tables(jwt_payload: dict, schema_name: str) -> dict:
        """
        List all tables and their type given a schema.

        :param jwt_payload: Dictionary containing databaseAddress, username, and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema to list all tables from
        :type schema_name: str
        :return: Contains a key for each table type where values are the respective list of
            table names
        :rtype: dict
        """
        _DJConnector._set_datajoint_config(jwt_payload)

        # Get list of tables names
        tables_name = dj.Schema(schema_name, create_schema=False).list_tables()
        # Dict to store list of table name for each type
        tables_dict_list = dict(manual=[], lookup=[], computed=[],
                                imported=[], part=[])
        # Loop through each table name to figure out what type it is and add them to
        # tables_dict_list
        for table_name in tables_name:
            table_type = dj.diagram._get_tier(
                '`' + schema_name + '`.`' + table_name + '`').__name__
            if table_type == 'Manual':
                tables_dict_list['manual'].append(dj.utils.to_camel_case(table_name))
            elif table_type == 'Lookup':
                tables_dict_list['lookup'].append(dj.utils.to_camel_case(table_name))
            elif table_type == 'Computed':
                tables_dict_list['computed'].append(dj.utils.to_camel_case(table_name))
            elif table_type == 'Imported':
                tables_dict_list['imported'].append(dj.utils.to_camel_case(table_name))
            elif table_type == 'Part':
                table_name_parts = table_name.split('__')
                tables_dict_list['part'].append(
                    to_camel_case(table_name_parts[-2]) + '.' +
                    to_camel_case(table_name_parts[-1]))
            else:
                raise UnsupportedTableType(table_name + ' is of unknown table type')
        return tables_dict_list

    @staticmethod
    def _fetch_records(query,
                       restriction: list = [], limit: int = 1000, page: int = 1,
                       order=['KEY ASC']) -> tuple:
        """
        Get records from query.

        :param query: any datajoint object related to QueryExpression
        :type query: datajoint ``QueryExpression`` or related object
        :param restriction: Sequence of filters as ``dict`` with ``attributeName``,
            ``operation``, ``value`` keys defined, defaults to ``[]``
        :type restriction: list, optional
        :param limit: Max number of records to return, defaults to ``1000``
        :type limit: int, optional
        :param page: Page number to return, defaults to ``1``
        :type page: int, optional
        :param order: Sequence to order records, defaults to ``['KEY ASC']``. See
            :class:`~datajoint.fetch.Fetch` for more info.
        :type order: list, optional
        :return: Attribute headers, records in dict form, and the total number of records that
            can be paged
        :rtype: tuple
        """

        # Get table object from name
        attributes = query.heading.attributes
        # Fetch tuples without blobs as dict to be used to create a
        #   list of tuples for returning
        query_restricted = query & dj.AndList([
            _DJConnector._filter_to_restriction(f, attributes[f['attributeName']].type)
            for f in restriction])
        non_blobs_rows = query_restricted.fetch(*query.heading.non_blobs, as_dict=True,
                                                limit=limit, offset=(page-1)*limit,
                                                order_by=order)

        # Buffer list to be return
        rows = []

        # Looped through each tuple and deal with TEMPORAL types and replacing
        #   blobs with ==BLOB== for json encoding
        for non_blobs_row in non_blobs_rows:
            # Buffer object to store the attributes
            row = []
            # Loop through each attributes, append to the tuple_to_return with specific
            #   modification based on data type
            for attribute_name, attribute_info in attributes.items():
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
        return list(attributes.keys()), rows, len(query_restricted)

    @staticmethod
    def _get_attributes(query) -> dict:
        """
        Method to get primary and secondary attributes of a query.

        :param query: any datajoint object related to QueryExpression
        :type query: datajoint ``QueryExpression`` or related object
        :return: Dict with keys ``attribute_headers`` and ``attributes`` containing
            ``primary``, ``secondary`` which each contain a
            ``list`` of ``tuples`` specifying: ``attribute_name``, ``type``, ``nullable``,
            ``default``, ``autoincrement``.
        :rtype: dict
        """

        query_attributes = dict(primary=[], secondary=[])
        for attribute_name, attribute_info in query.heading.attributes.items():
            if attribute_info.in_key:
                query_attributes['primary'].append((
                    attribute_name,
                    attribute_info.type,
                    attribute_info.nullable,
                    attribute_info.default,
                    attribute_info.autoincrement
                    ))
            else:
                query_attributes['secondary'].append((
                    attribute_name,
                    attribute_info.type,
                    attribute_info.nullable,
                    attribute_info.default,
                    attribute_info.autoincrement
                    ))

        return dict(attribute_headers=['name', 'type', 'nullable',
                                       'default', 'autoincrement'],
                    attributes=query_attributes)

    @staticmethod
    def _get_table_definition(jwt_payload: dict, schema_name: str, table_name: str) -> str:
        """
        Get the table definition.

        :param jwt_payload: Dictionary containing databaseAddress, username, and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :return: Definition of the table
        :rtype: str
        """
        _DJConnector._set_datajoint_config(jwt_payload)

        local_values = locals()
        local_values[schema_name] = dj.VirtualModule(schema_name, schema_name)
        return getattr(local_values[schema_name], table_name).describe()

    @staticmethod
    def _insert_tuple(jwt_payload: dict, schema_name: str, table_name: str,
                      tuple_to_insert: dict):
        """
        Insert record as tuple into table.

        :param jwt_payload: Dictionary containing databaseAddress, username, and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :param tuple_to_insert: Record to be inserted
        :type tuple_to_insert: dict
        """
        _DJConnector._set_datajoint_config(jwt_payload)

        schema_virtual_module = dj.VirtualModule(schema_name, schema_name)
        getattr(schema_virtual_module, table_name).insert(tuple_to_insert)

    @staticmethod
    def _record_dependency(jwt_payload: dict, schema_name: str, table_name: str,
                           restriction: list = []) -> list:
        """
        Return summary of dependencies associated with a restricted table. Will only show
        dependencies that user has access to.

        :param jwt_payload: Dictionary containing databaseAddress, username, and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :param restriction: Sequence of filters as ``dict`` with ``attributeName``,
            ``operation``, ``value`` keys defined, defaults to ``[]``
        :type restriction: list
        :return: Tables that are dependent on specific records.
        :rtype: list
        """
        _DJConnector._set_datajoint_config(jwt_payload)
        virtual_module = dj.VirtualModule(schema_name, schema_name)
        table = getattr(virtual_module, table_name)
        attributes = table.heading.attributes
        # Retrieve dependencies of related to retricted
        dependencies = [dict(schema=descendant.database, table=descendant.table_name,
                             accessible=True, count=len(
                                (table if descendant.full_table_name == table.full_table_name
                                 else descendant * table) & dj.AndList([
                                    _DJConnector._filter_to_restriction(
                                        f, attributes[f['attributeName']].type)
                                    for f in restriction])))
                        for descendant in table().descendants(as_objects=True)]
        return dependencies

    @staticmethod
    def _update_tuple(jwt_payload: dict, schema_name: str, table_name: str,
                      tuple_to_update: dict):
        """
        Update record as tuple into table.

        :param jwt_payload: Dictionary containing databaseAddress, username, and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :param tuple_to_update: Record to be updated
        :type tuple_to_update: dict
        """
        conn = _DJConnector._set_datajoint_config(jwt_payload)

        schema_virtual_module = dj.VirtualModule(schema_name, schema_name)
        with conn.transaction:
            [getattr(schema_virtual_module, table_name).update1(t) for t in tuple_to_update]

    @staticmethod
    def _delete_records(jwt_payload: dict, schema_name: str, table_name: str,
                        restriction: list = [], cascade: bool = False):
        """
        Delete a specific record based on the restriction given.

        :param jwt_payload: Dictionary containing databaseAddress, username, and password
            strings
        :type jwt_payload: dict
        :param schema_name: Name of schema
        :type schema_name: str
        :param table_name: Table name under the given schema; must be in camel case
        :type table_name: str
        :param restriction: Sequence of filters as ``dict`` with ``attributeName``,
            ``operation``, ``value`` keys defined, defaults to ``[]``
        :type restriction: list, optional
        :param cascade: Allow for cascading delete, defaults to ``False``
        :type cascade: bool, optional
        """
        _DJConnector._set_datajoint_config(jwt_payload)

        schema_virtual_module = dj.VirtualModule(schema_name, schema_name)

        # Get table object from name
        table = _DJConnector._get_table_object(schema_virtual_module, table_name)
        attributes = table.heading.attributes
        restrictions = [
            _DJConnector._filter_to_restriction(f, attributes[f['attributeName']].type)
            for f in restriction]

        # Compute restriction
        query = table & dj.AndList(restrictions)
        # Check if there is only 1 tuple to delete otherwise raise error
        if len(query) == 0:
            raise InvalidRestriction('Nothing to delete')

        # All check pass thus proceed to delete
        query.delete(safemode=False) if cascade else query.delete_quick()

    @staticmethod
    def _get_table_object(schema_virtual_module: VirtualModule, table_name: str) -> UserTable:
        """
        Helper method for getting the table object based on the table name provided.

        :param schema_virtual_module: Virtual module for accesing the schema
        :type schema_virtual_module: :class:`~datajoint.schemas.VirtualModule`
        :param table_name: Name of the table; for part it should be ``Parent.Part``
        :type table_name: str
        :return: DataJoint table object.
        :rtype: :class:`~datajoint.user_tables.UserTable`
        """
        # Split the table name by '.' for dealing with part tables
        table_name_parts = table_name.split('.')
        if len(table_name_parts) == 2:
            return getattr(getattr(schema_virtual_module, table_name_parts[0]),
                           table_name_parts[1])
        else:
            return getattr(schema_virtual_module, table_name_parts[0])

    @staticmethod
    def _filter_to_restriction(attribute_filter: dict, attribute_type: str) -> str:
        """
        Convert attribute filter to a restriction.

        :param attribute_filter: A filter as ``dict`` with ``attributeName``, ``operation``,
            ``value`` keys defined, defaults to ``[]``
        :type attribute_filter: dict
        :param attribute_type: Attribute type
        :type attribute_type: str
        :return: DataJoint-compatible restriction
        :rtype: str
        """
        if attribute_filter['operation'] in ('>', '<', '>=', '<='):
            operation = attribute_filter['operation']
        elif attribute_filter['value'] is None:
            operation = (' IS ' if attribute_filter['operation'] == '='
                         else ' IS NOT ')
        else:
            operation = attribute_filter['operation']

        if (isinstance(attribute_filter['value'], str) and
                not attribute_filter['value'].isnumeric()):
            value = (f"X'{attribute_filter['value'].replace('-', '')}'"
                     if attribute_type == 'uuid' else f"'{attribute_filter['value']}'")
        else:
            value = ('NULL' if attribute_filter['value'] is None
                     else attribute_filter['value'])
        return f"{attribute_filter['attributeName']}{operation}{value}"

    @staticmethod
    def _set_datajoint_config(jwt_payload: dict) -> dj.connection.Connection:
        """
        Method to set credentials for database.

        :param jwt_payload: Dictionary containing databaseAddress, username, and password
            strings
        :type jwt_payload: dict
        :return: DataJoint connection object.
        :rtype: :class:`~datajoint.connection.Connection`
        """
        dj.config['database.host'] = jwt_payload['databaseAddress']
        dj.config['database.user'] = jwt_payload['username']
        dj.config['database.password'] = jwt_payload['password']
        return dj.conn(reset=True)
