"""
Tests for the JESI data cleaning module.
JAS Unified Economic Strength Index (JESI)
Master Version 1.0
"""

import pandas as pd

from src.data_cleaning import (
    validate_required_columns,
    convert_value_to_numeric,
    remove_duplicate_records,
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


def test_remove_duplicate_records():
    """
    Duplicate observations should be removed.
    """

    dataframe = pd.DataFrame(
        {
            "country": [
                "Bangladesh",
                "Bangladesh",
                "India",
            ],
            "year": [
                2023,
                2023,
                2023,
            ],
            "value": [
                6.0,
                6.0,
                7.0,
            ],
        }
    )

    result = remove_duplicate_records(
        dataframe
    )

    assert len(result) == 2
    assert result.iloc[0]["country"] == "Bangladesh"
    assert result.iloc[1]["country"] == "India"
