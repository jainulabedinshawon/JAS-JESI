"""
Tests for the JESI data cleaning module.
JAS Unified Economic Strength Index (JESI)
Master Version 1.0
"""

import pandas as pd

from src.data_cleaning import (
    validate_required_columns,
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
