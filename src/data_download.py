"""
JESI Data Download Module
JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This module provides reproducible functions for downloading
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

    response = requests.get(
        url,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if len(data) < 2 or not data[1]:
        return pd.DataFrame(
            columns=[
                "country",
                "year",
                "value",
                "indicator",
            ]
        )

    records = []

    for item in data[1]:
        records.append(
            {
                "country": item.get(
                    "country",
                    {},
                ).get(
                    "value"
                ),
                "year": int(item["date"]),
                "value": item.get("value"),
                "indicator": indicator,
            }
        )

    return pd.DataFrame(records)


def save_dataframe(
    dataframe,
    filepath,
):
    """
    Save downloaded data to a CSV file.
    """

    dataframe.to_csv(
        filepath,
        index=False,
    )


def download_multiple_indicators(
    country,
    indicators,
    start_year,
    end_year,
):
    """
    Download multiple World Bank indicators
    for a single country and combine them
    into a single DataFrame.
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

    return pd.concat(
        frames,
        ignore_index=True,
    )


def download_country_indicators(
    countries,
    indicators,
    start_year,
    end_year,
):
    """
    Download multiple indicators for multiple countries.

    Parameters
    ----------
    countries : list
        ISO3 country codes,
        e.g. ["BGD", "IND", "VNM"].

    indicators : list
        World Bank indicator codes.

    start_year : int
        First year of the requested period.

    end_year : int
        Last year of the requested period.

    Returns
    -------
    pandas.DataFrame
        Combined country-level indicator data.
    """

    frames = []

    for country in countries:
        data = download_multiple_indicators(
            country=country,
            indicators=indicators,
            start_year=start_year,
            end_year=end_year,
        )

        frames.append(data)

    if not frames:
        return pd.DataFrame(
            columns=[
                "country",
                "year",
                "value",
                "indicator",
            ]
        )

    return pd.concat(
        frames,
        ignore_index=True,
    )


def download_productivity_data(
    countries,
    start_year,
    end_year,
):
    """
    Download the World Bank GDP per person employed
    indicator for multiple countries.

    Indicator:
        SL.GDP.PCAP.EM.KD

    Unit:
        Constant 2021 PPP dollars.
    """

    return download_country_indicators(
        countries=countries,
        indicators=[
            "SL.GDP.PCAP.EM.KD",
        ],
        start_year=start_year,
        end_year=end_year,
    )


def calculate_tfp_growth(
    dataframe,
):
    """
    Calculate annual TFP growth from PWT TFP levels.

    Expected columns:
        country
        year
        tfp

    Returns
    -------
    pandas.DataFrame
        Country-year TFP growth data.
    """

    dataframe = dataframe.copy()

    dataframe = dataframe.sort_values(
        [
            "country",
            "year",
        ]
    )

    dataframe["tfp_growth"] = (
        dataframe
        .groupby("country")["tfp"]
        .pct_change()
        * 100
    )

    return dataframe
