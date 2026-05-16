"""Parser-specific exception hierarchy."""


class ParserError(Exception):
    """Base exception for parser failures."""


class ParserNotSupportedError(ParserError):
    """Raised when no parser can handle a given URL."""
