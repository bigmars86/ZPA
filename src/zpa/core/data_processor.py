"""
Datetime parsing helpers for Zoom Poll Analyzer.
"""

from datetime import datetime
from typing import Optional


def parse_iso_datetime(dt_string: str) -> Optional[datetime]:
    """Parse ISO datetime string, handling Zoom's 'Z' suffix format

    Args:
        dt_string: ISO datetime string, possibly ending with 'Z'

    Returns:
        datetime object or None if parsing fails
    """
    try:
        return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
