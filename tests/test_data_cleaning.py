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
    sort_by_country_and_year,
    remove_invalid_years,
    validate_missing_values,
    clean_indicator_data,
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


def test_sort_by_country_and_year():
    """
    Records should be sorted by country and year.
    """

    dataframe = pd.DataFrame(
        {
            "country": [
                "India",
                "Bangladesh",
                "Bangladesh",
            ],
            "year": [
                2023,
                2024,
                2023,
            ],
            "value": [
                7.0,
                6.5,
                6.0,
            ],
        }
    )

    result = sort_by_country_and_year(
        dataframe
    )

    assert list(result["country"]) == [
        "Bangladesh",
        "Bangladesh",
        "India",
    ]

    assert list(result["year"]) == [
        2023,
        2024,
        2023,
    ]


def test_remove_invalid_years():
    """
    Invalid year observations should be removed.
    """

    dataframe = pd.DataFrame(
        {
            "country": [
                "Bangladesh",
                "India",
                "Nepal",
                "Pakistan",
            ],
            "year": [
                2023,
                1899,
                2101,
                2024,
            ],
            "value": [
                6.0,
                7.0,
                5.0,
                6.5,
            ],
        }
    )

    result = remove_invalid_years(
        dataframe
    )

    assert list(result["year"]) == [
        2023,
        2024,
    ]


def test_validate_missing_values():
    """
    Missing values should be counted correctly.
    """

    dataframe = pd.DataFrame(
        {
            "value": [
                6.0,
                None,
                7.5,
                None,
            ]
        }
    )

    result = validate_missing_values(
        dataframe,
        "value",
    )

    assert result == 2


def test_validate_missing_values_does_not_modify_data():
    """
    Missing-value validation should not modify the data.
    """

    dataframe = pd.DataFrame(
        {
            "value": [
                6.0,
                None,
                7.5,
            ]
        }
    )

    result = validate_missing_values(
        dataframe,
        "value",
    )

    assert result == 1
    assert pd.isna(dataframe["value"].iloc[1])


def test_clean_indicator_data():
    """
    The complete JESI cleaning pipeline should
    convert values, remove duplicates and invalid
    years, and sort the observations.
    """

    dataframe = pd.DataFrame(
        {
            "country": [
                "India",
                "Bangladesh",
                "Bangladesh",
                "Nepal",
            ],
            "year": [
                2023,
                2024,
                2024,
                1899,
            ],
            "value": [
                "7.0",
                "6.5",
                "6.5",
                "5.0",
            ],
        }
    )

    result = clean_indicator_data(
        dataframe,
        required_columns=[
            "country",
            "year",
            "value",
        ],
    )

    assert len(result) == 2

    assert list(result["country"]) == [
        "Bangladesh",
        "India",
    ]

    assert list(result["year"]) == [
        2024,
        2023,
    ]

    assert list(result["value"]) == [
        6.5,
        7.0,
    ]
