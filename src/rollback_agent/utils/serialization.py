"""Utility functions for serialization."""
from datetime import datetime
from .time_utils import serialize_datetimes as _serialize_dt


def serialize_datetimes(obj, fmt: str = None, tz_name: str = None):
    """Recursively convert datetime objects to strings using configured format and timezone."""
    return _serialize_dt(obj, fmt=fmt, tz_name=tz_name)