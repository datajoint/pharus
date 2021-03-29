"""Error class library."""


class UnsupportedTableType(Exception):
    """Exception raised on unsupported table types."""
    pass


class InvalidDeleteRequest(Exception):
    """Exception raised when attempting to delete 0 records."""
    pass
