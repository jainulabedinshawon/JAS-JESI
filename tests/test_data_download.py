"""
Tests for the JESI data download module.
JAS Unified Economic Strength Index (JESI)
Master Version 1.0
"""

import pandas as pd

from src.data_download import (
    download_world_bank_indicator,
    download_multiple_indicators,
    download_country_indicators,
)


def test_download_world_bank_indicator(monkeypatch):
    """
    Test World Bank indicator download using
    a mocked API response.
    """

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {
                    "page": 1,
                    "pages": 1,
                },
                [
                    {
                        "country": {
                            "value": "Bangladesh"
                        },
                        "date": "2023",
                        "value": 6.0,
                    }
                ],
            ]

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(
        "src.data_download.requests.get",
        mock_get,
    )

    result = download_world_bank_indicator(
        country="BGD",
        indicator="NY.GDP.MKTP.KD.ZG",
        start_year=2023,
        end_year=2023,
    )

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1
    assert result.iloc[0]["country"] == "Bangladesh"
    assert result.iloc[0]["year"] == 2023
    assert result.iloc[0]["value"] == 6.0
    assert result.iloc[0]["indicator"] == "NY.GDP.MKTP.KD.ZG"


def test_download_world_bank_indicator_empty(monkeypatch):
    """
    Test that an empty World Bank response
    returns an empty DataFrame.
    """

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {
                    "page": 1,
                    "pages": 1,
                },
                [],
            ]

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(
        "src.data_download.requests.get",
        mock_get,
    )

    result = download_world_bank_indicator(
        country="BGD",
        indicator="INVALID",
        start_year=2023,
        end_year=2023,
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert list(result.columns) == [
        "country",
        "year",
        "value",
        "indicator",
    ]


def test_download_multiple_indicators(monkeypatch):
    """
    Test downloading and combining multiple indicators.
    """

    def mock_download(
        country,
        indicator,
        start_year,
        end_year,
    ):
        return pd.DataFrame(
            [
                {
                    "country": "Bangladesh",
                    "year": 2023,
                    "value": 6.0,
                    "indicator": indicator,
                }
            ]
        )

    monkeypatch.setattr(
        "src.data_download.download_world_bank_indicator",
        mock_download,
    )

    result = download_multiple_indicators(
        country="BGD",
        indicators=[
            "NY.GDP.MKTP.KD.ZG",
            "NY.GDP.PCAP.KD.ZG",
        ],
        start_year=2023,
        end_year=2023,
    )

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert set(result["indicator"]) == {
        "NY.GDP.MKTP.KD.ZG",
        "NY.GDP.PCAP.KD.ZG",
    }


def test_download_country_indicators(monkeypatch):
    """
    Test downloading multiple indicators for multiple countries.
    """

    def mock_download_multiple(
        country,
        indicators,
        start_year,
        end_year,
    ):
        records = []

        for indicator in indicators:
            records.append(
                {
                    "country": country,
                    "year": 2023,
                    "value": 6.0,
                    "indicator": indicator,
                }
            )

        return pd.DataFrame(records)

    monkeypatch.setattr(
        "src.data_download.download_multiple_indicators",
        mock_download_multiple,
    )

    result = download_country_indicators(
        countries=[
            "BGD",
            "IND",
        ],
        indicators=[
            "NY.GDP.MKTP.KD.ZG",
            "NY.GDP.PCAP.KD.ZG",
        ],
        start_year=2023,
        end_year=2023,
    )

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 4

    assert set(result["country"]) == {
        "BGD",
        "IND",
    }

    assert set(result["indicator"]) == {
        "NY.GDP.MKTP.KD.ZG",
        "NY.GDP.PCAP.KD.ZG",
    }

    assert all(result["year"] == 2023)
