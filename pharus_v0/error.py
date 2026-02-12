"""Error class library."""


class UnsupportedTableType(Exception):
    """Exception raised on unsupported table types."""

    pass


class InvalidRestriction(Exception):
    """Exception raised when restrictions result in no records when expected at least one."""

    pass


class SchemaNotFound(Exception):
    """Exception raised when a given schema is not found to exist"""

    pass


class TableNotFound(Exception):
    """Exception raised when a given table is not found to exist"""

    pass
