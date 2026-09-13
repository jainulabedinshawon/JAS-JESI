"""
Tests for the JESI data cleaning module.
JAS Unified Economic Strength Index (JESI)
Master Version 1.0
"""

import pandas as pd

from src.data_cleaning import (
    validate_required_columns,
    convert_value_to_numeric,
)


def test_validate_required_columns_success():
    """
    Required columns should be accepted
    when all are present.
    """

    dataframe = pd.DataFrame(
        {
            "country": ["Bangladesh"],
            "year": [2023],
            "value": [6.0],
        }
    )

    result = validate_required_columns(
        dataframe,
        ["country", "year", "value"],
    )

    assert result is True


def test_convert_value_to_numeric():
    """
    Indicator values should be converted to numeric values.
    Invalid values should become NaN.
    """

    dataframe = pd.DataFrame(
        {
            "value": ["6.0", "7.5", "invalid"],
        }
    )

    result = convert_value_to_numeric(
        dataframe,
        "value",
    )

    assert result["value"].iloc[0] == 6.0
    assert result["value"].iloc[1] == 7.5
    assert pd.isna(result["value"].iloc[2])
