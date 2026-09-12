"""
JESI Data Cleaning Module
JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This module provides basic, reproducible data-cleaning
functions for JESI economic indicators.
"""

import pandas as pd


def validate_required_columns(dataframe, required_columns):
    """
    Check whether all required columns exist.
    """
    missing = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    return True


def convert_value_to_numeric(dataframe, column):
    """
    Convert an indicator column to numeric values.

    Invalid or non-numeric observations become NaN.
    """
    dataframe = dataframe.copy()

    dataframe[column] = pd.to_numeric(
        dataframe[column],
        errors="coerce",
    )

    return dataframe


def remove_duplicate_records(
    dataframe,
    subset=None,
):
    """
    Remove duplicate observations.
    """
    return dataframe.drop_duplicates(
        subset=subset
    ).reset_index(drop=True)


def sort_by_country_and_year(dataframe):
    """
    Sort observations by country and year
    when those columns are available.
    """
    dataframe = dataframe.copy()

    columns = [
        column
        for column in ["country", "year"]
        if column in dataframe.columns
    ]

    if columns:
        dataframe = dataframe.sort_values(
            columns
        ).reset_index(drop=True)

    return dataframe


def remove_invalid_years(
    dataframe,
    minimum_year=1900,
    maximum_year=2100,
):
    """
    Remove observations with invalid year values.
    """
    dataframe = dataframe.copy()

    if "year" not in dataframe.columns:
        return dataframe

    dataframe["year"] = pd.to_numeric(
        dataframe["year"],
        errors="coerce",
    )

    dataframe = dataframe[
        dataframe["year"].between(
            minimum_year,
            maximum_year,
        )
    ]

    dataframe["year"] = dataframe["year"].astype(int)

    return dataframe.reset_index(drop=True)


def clean_indicator_data(
    dataframe,
    required_columns=None,
):
    """
    Apply the basic JESI data-cleaning pipeline.
    """
    dataframe = dataframe.copy()

    if required_columns:
        validate_required_columns(
            dataframe,
            required_columns,
        )

    if "value" in dataframe.columns:
        dataframe = convert_value_to_numeric(
            dataframe,
            "value",
        )

    dataframe = remove_duplicate_records(
        dataframe
    )

    dataframe = remove_invalid_years(
        dataframe
    )

    dataframe = sort_by_country_and_year(
        dataframe
    )

    return dataframe
