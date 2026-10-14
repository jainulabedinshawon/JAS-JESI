"""End-to-end synthetic regression tests for the JESI scoring path.

These tests cover the current scalar normalization functions and the
Master Version 1.0 fixed-weight scorer. They do not claim that PCA
weights are currently part of the production scoring path.
"""

import math

import pytest

from src.jesi_calculation import (
WEIGHTS,
calculate_jesi,
validate_pillar_scores,
)
from src.normalization import (
normalize_positive,
normalize_negative,
normalize_positive_clipped,
normalize_negative_clipped,
)

def test_master_version_weights_cover_exactly_five_pillars():
assert set(WEIGHTS) == {"G", "P", "C", "R", "A"}
assert all(0 < weight < 1 for weight in WEIGHTS.values())
assert math.isclose(
sum(WEIGHTS.values()), 1.0, rel_tol=0.0, abs_tol=1e-12
)

@pytest.mark.parametrize(
("function", "value", "minimum", "maximum", "expected"),
[
(normalize_positive, 10, 10, 30, 0.0),
(normalize_positive, 20, 10, 30, 0.5),
(normalize_positive, 30, 10, 30, 1.0),
(normalize_negative, 30, 10, 30, 0.0),
(normalize_negative, 20, 10, 30, 0.5),
(normalize_negative, 10, 10, 30, 1.0),
],
)
def test_normalization_direction_and_endpoints(
function, value, minimum, maximum, expected
):
assert function(value, minimum, maximum) == pytest.approx(expected)

@pytest.mark.parametrize(
"function",
[
normalize_positive,
normalize_negative,
normalize_positive_clipped,
normalize_negative_clipped,
],
)
def test_normalization_rejects_zero_range(function):
with pytest.raises(ValueError, match="equal"):
function(5, 5, 5)

@pytest.mark.parametrize(
("function", "value", "expected"),
[
(normalize_positive_clipped, -5, 0.0),
(normalize_positive_clipped, 15, 1.0),
(normalize_negative_clipped, 15, 0.0),
(normalize_negative_clipped, -5, 1.0),
],
)
def test_clipped_normalization_bounds_out_of_range_values(
function, value, expected
):
assert function(value, 0, 10) == pytest.approx(expected)

def _synthetic_indicator_to_jesi_pipeline():
"""Normalize synthetic indicators, construct five pillars, calculate JESI.

Each pillar is represented by one higher-is-better and one
lower-is-better indicator. The arithmetic mean is used only to create
a deterministic synthetic fixture; it does not assert that every
empirical pillar-construction script uses this aggregation method.
"""
raw = {
    "G": {"positive": (10, 20, 50), "negative": (30, 20, 10)},
    "P": {"positive": (2, 5, 10), "negative": (90, 50, 10)},
    "C": {"positive": (5, 15, 25), "negative": (80, 60, 20)},
    "R": {"positive": (1, 4, 9), "negative": (70, 40, 10)},
    "A": {"positive": (3, 8, 18), "negative": (100, 60, 20)},
}

pillars = {}

# Use the middle observation in each synthetic three-observation set.
for pillar, indicators in raw.items():
    positive_values = indicators["positive"]
    negative_values = indicators["negative"]

    positive_score = normalize_positive(
        positive_values[1],
        min(positive_values),
        max(positive_values),
    )
    negative_score = normalize_negative(
        negative_values[1],
        min(negative_values),
        max(negative_values),
    )

    pillars[pillar] = (positive_score + negative_score) / 2

return pillars, calculate_jesi(pillars)

def test_synthetic_indicator_to_pillar_to_jesi_pipeline():
pillars, score = _synthetic_indicator_to_jesi_pipeline()

assert set(pillars) == {"G", "P", "C", "R", "A"}
assert all(0 <= value <= 1 for value in pillars.values())
assert math.isfinite(score)
assert 0 <= score <= 100

def test_all_five_pillars_are_required():
valid = {"G": 0.8, "P": 0.7, "C": 0.6, "R": 0.9, "A": 0.5}
validate_pillar_scores(valid)

for missing_pillar in valid:
    incomplete = dict(valid)
    del incomplete[missing_pillar]

    with pytest.raises(ValueError):
        calculate_jesi(incomplete)

def test_extra_pillar_is_rejected():
pillars = {
"G": 0.8,
"P": 0.7,
"C": 0.6,
"R": 0.9,
"A": 0.5,
"X": 0.4,
}

with pytest.raises(ValueError):
    calculate_jesi(pillars)

@pytest.mark.parametrize("bad_score", [-0.01, 1.01])
def test_out_of_range_pillar_is_rejected(bad_score):
pillars = {"G": 0.8, "P": 0.7, "C": 0.6, "R": 0.9, "A": 0.5}
pillars["A"] = bad_score

with pytest.raises(ValueError):
    calculate_jesi(pillars)

def test_each_pillar_influences_final_score():
baseline = {"G": 0.8, "P": 0.7, "C": 0.6, "R": 0.9, "A": 0.5}
baseline_score = calculate_jesi(baseline)

for pillar in baseline:
    changed = dict(baseline)
    changed[pillar] = min(1.0, changed[pillar] + 0.1)

    assert calculate_jesi(changed) > baseline_score

def test_zero_pillar_score_produces_zero_jesi():
pillars = {"G": 0.8, "P": 0.7, "C": 0.6, "R": 0.9, "A": 0.0}

assert calculate_jesi(pillars) == pytest.approx(0.0)
