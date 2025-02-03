class FlightSearchError(Exception):
    """Base exception for flight search errors."""

    pass


class InvalidFlightClassError(FlightSearchError):
    """Exception raised for invalid flight classes."""

    pass


class InvalidPassengerCountError(FlightSearchError):
    """Exception raised for invalid passenger counts."""

    pass


class InvalidAirportCodeError(FlightSearchError):
    """Exception raised for invalid airport codes."""

    pass


class DateConversionError(FlightSearchError):
    """Exception raised for date conversion failures."""

    pass
