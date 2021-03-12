"""Error class library."""


class UnsupportedTableType(Exception):
    """Exception raised on unsupported table types."""
    pass


class InvalidRestriction(Exception):
    """Exception raised when restrictions result in no records when expected at least one."""
    pass


class InvalidDeleteRequest(Exception):
    """Exception raised when attempting to delete >1 or <1 records."""
    pass
