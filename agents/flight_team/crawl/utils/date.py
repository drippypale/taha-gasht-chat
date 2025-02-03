import jdatetime
from datetime import datetime
from agents.flight_team.crawl.exceptions import DateConversionError


def convert_to_gregorian(date_str: str) -> str:
    """
    Convert a date string from Jalali to Gregorian if necessary.

    Args:
        date_str (str): Date string in 'YYYY-MM-DD' format.

    Returns:
        str: Gregorian date string in 'YYYY-MM-DD' format.

    Raises:
        DateConversionError: If the date format is invalid or conversion fails.
    """
    try:
        year = int(date_str.split("-")[0])
        if year > 1400 and year < 2000:
            jalali_date = jdatetime.datetime.strptime(date_str, "%Y-%m-%d")
            gregorian_date = jalali_date.togregorian()
            return gregorian_date.strftime("%Y-%m-%d")
        else:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
    except (ValueError, jdatetime.errors.JDValueError) as e:
        raise DateConversionError(f"Failed to convert date '{date_str}': {e}")
