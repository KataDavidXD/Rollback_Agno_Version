"""Time and datetime utilities with configurable timezone and format."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from zoneinfo import ZoneInfo

# User-configurable settings
# Change these to your preference
USER_TIMEZONE_NAME: str = "Asia/Shanghai"  # "Shanghai"
USER_DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S"  # Example -> 2025-08-11T13:44:36


def get_timezone(tz_name: Optional[str] = None) -> ZoneInfo:
    """Return ZoneInfo for the given timezone name, defaulting to user setting."""
    return ZoneInfo(tz_name or USER_TIMEZONE_NAME)


def now(tz_name: Optional[str] = None) -> datetime:
    """Return current time in the configured timezone."""
    return datetime.now(get_timezone(tz_name))


def parse_datetime(value: Union[str, datetime], tz_name: Optional[str] = None) -> datetime:
    """Parse a datetime from string or pass-through, then ensure it's in the target timezone.

    - Accepts ISO 8601 strings (including trailing 'Z') and common legacy formats
    - If no timezone info, assumes the configured timezone
    - If timezone is present, converts to target timezone
    """
    target_tz = get_timezone(tz_name)

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        raw = value
        dt: Optional[datetime] = None
        # Try ISO 8601 first
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            # Fallbacks: common formats
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
                try:
                    dt = datetime.strptime(raw, fmt)
                    break
                except ValueError:
                    continue
        if dt is None:
            raise ValueError(f"Unrecognized datetime format: {value}")
    else:
        raise TypeError(f"Unsupported datetime value type: {type(value)}")

    # Ensure timezone awareness and convert to target timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=target_tz)
    else:
        dt = dt.astimezone(target_tz)
    return dt


def format_datetime(dt: datetime, fmt: Optional[str] = None, tz_name: Optional[str] = None) -> str:
    """Format datetime into string in the chosen timezone and format."""
    fmt_to_use = fmt or USER_DATETIME_FORMAT
    # Convert to target timezone first
    dt_in_tz = dt if dt.tzinfo is not None else dt.replace(tzinfo=get_timezone(tz_name))
    dt_in_tz = dt_in_tz.astimezone(get_timezone(tz_name))
    return dt_in_tz.strftime(fmt_to_use)


def serialize_datetimes(obj: Any, fmt: Optional[str] = None, tz_name: Optional[str] = None) -> Any:
    """Recursively convert datetime objects to formatted strings in desired timezone."""
    if isinstance(obj, datetime):
        return format_datetime(obj, fmt=fmt, tz_name=tz_name)
    if isinstance(obj, dict):
        return {k: serialize_datetimes(v, fmt=fmt, tz_name=tz_name) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_datetimes(item, fmt=fmt, tz_name=tz_name) for item in obj]
    return obj


