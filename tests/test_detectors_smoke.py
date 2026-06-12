"""
Smoke tests: the registered detectors actually execute on a small data fixture.

The fixture (tests/fixtures/nq_sample.csv) is a 1000-row slice of real NQ 1m data
committed to the repo so tests run on a fresh clone without the full dataset.
"""
import pathlib

import pandas as pd
import pytest

from ict.concepts.fair_value_gap import find_fvgs
from ict.concepts.market_structure import SwingPointScanner

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "nq_sample.csv"


@pytest.fixture
def nq_1m() -> pd.DataFrame:
    df = pd.read_csv(FIXTURE, parse_dates=["timestamp"])
    return df.set_index("timestamp").sort_index()


def test_fixture_present_and_shaped(nq_1m):
    assert len(nq_1m) == 1000
    assert {"open", "high", "low", "close"} <= set(nq_1m.columns)


def test_find_fvgs_runs(nq_1m):
    out = find_fvgs(nq_1m, direction="bearish")
    assert isinstance(out, list)


def test_swing_scanner_constructs(nq_1m):
    # API surface beyond construction isn't pinned here; this just confirms the
    # registered detector is importable and runs on the fixture frame.
    scanner = SwingPointScanner(nq_1m)
    assert scanner is not None
