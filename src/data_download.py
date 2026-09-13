"""
JESI Data Download Module
JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This module provides basic functions for downloading
economic indicator data from public APIs.
"""

import requests
import pandas as pd


WORLD_BANK_API = "https://api.worldbank.org/v2/country"


def download_world_bank_indicator(
    country,
    indicator,
    start_year,
    end_year,
):
    """
    Download a World Bank indicator for a country
    over a specified year range.

    Parameters
    ----------
    country : str
        World Bank country code, e.g. "BGD".

    indicator : str
        World Bank indicator code.

    start_year : int
        First year.

    end_year : int
        Last year.

    Returns
    -------
    pandas.DataFrame
        Country, year, indicator value, and indicator code.
    """

    url = (
        f"{WORLD_BANK_API}/{country}/indicator/"
        f"{indicator}?format=json&per_page=100"
        f"&date={start_year}:{end_year}"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    if len(data) < 2 or not data[1]:
        return pd.DataFrame(
            columns=["country", "year", "value", "indicator"]
        )

    records = []

    for item in data[1]:
        records.append(
            {
                "country": item.get("country", {}).get("value"),
                "year": int(item["date"]),
                "value": item.get("value"),
                "indicator": indicator,
            }
        )

    return pd.DataFrame(records)


def save_dataframe(dataframe, filepath):
    """
    Save downloaded data to a CSV file.
    """
    dataframe.to_csv(filepath, index=False)


def download_multiple_indicators(
    country,
    indicators,
    start_year,
    end_year,
):
    """
    Download multiple World Bank indicators
    and combine them into a single DataFrame.
    """

    frames = []

    for indicator in indicators:
        data = download_world_bank_indicator(
            country=country,
            indicator=indicator,
            start_year=start_year,
            end_year=end_year,
        )

        frames.append(data)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)
