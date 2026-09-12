"""
JESI Normalization Module
JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This module provides reproducible normalization functions
for converting economic indicators to a 0–1 scale.
"""


def normalize_positive(value, minimum, maximum):
    """
    Normalize a positive-direction indicator.

    Higher values represent better performance.

    Formula:
        (value - minimum) / (maximum - minimum)
    """
    if maximum == minimum:
        raise ValueError("Maximum and minimum cannot be equal.")

    return (value - minimum) / (maximum - minimum)


def normalize_negative(value, minimum, maximum):
    """
    Normalize a negative-direction indicator.

    Lower values represent better performance.

    Formula:
        (maximum - value) / (maximum - minimum)
    """
    if maximum == minimum:
        raise ValueError("Maximum and minimum cannot be equal.")

    return (maximum - value) / (maximum - minimum)


def clip_normalized(value):
    """
    Keep a normalized value within the 0–1 range.
    """
    return max(0.0, min(1.0, value))


def normalize_positive_clipped(value, minimum, maximum):
    """
    Normalize a positive-direction indicator
    and constrain the result to 0–1.
    """
    return clip_normalized(
        normalize_positive(value, minimum, maximum)
    )


def normalize_negative_clipped(value, minimum, maximum):
    """
    Normalize a negative-direction indicator
    and constrain the result to 0–1.
    """
    return clip_normalized(
        normalize_negative(value, minimum, maximum)
    )
