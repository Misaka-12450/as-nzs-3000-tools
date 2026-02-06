from typing import Iterable, Literal, Sequence

import pytest

from iec60898 import IEC60898


_TEST_DATA_CURRENT_TO_TIME = [
    (2, "B", (3, 4), (30, 40)),
    (2, "C", (3, 4), (30, 40)),
    (3, "B", (1, 2), (10, 20)),
    (3, "C", (1, 2), (10, 20)),
    (4, "B", 0, (6, 7)),
    (4, "C", (0.8, 0.9), (6, 7)),
    (5, "B", 0, 0),
    (5, "C", (0.6, 0.7), (4, 5)),
    (6, "C", (0.5, 0.6), (3, 4)),
    (7, "C", 0, (3, 4)),
    (8, "C", 0, (2, 3)),
    (9, "C", 0, (2, 3)),
    (10, "C", 0, 0),
]

_TEST_DATA_TIME_TO_CURRENT = [
    (1, "B", 3.2, 4.8),
    (1, "C", 3.5, 9.5),
    (2, "B", 2.5, 4.8),
    (2, "C", 2.5, 9.5),
    (3, "B", 2.1, 4.8),
    (3, "C", 2.1, 7.5),
    (10, "C", 1.5, 3.3),
    (100, "C", 1.2, 1.6),
    (1000, "C", 1.1, 1.3),
]


@pytest.mark.parametrize(
    "i_ln,curve,min_expected,max_expected", _TEST_DATA_CURRENT_TO_TIME
)
def test_get_time_from_current(
    i_ln,
    curve: Literal["B", "C"],
    min_expected: int | float | Sequence[int | float],
    max_expected: int | float | Sequence[int | float],
):
    min_time, max_time = IEC60898.get_time_from_current(i_ln, curve)
    if isinstance(min_expected, Sequence) and not isinstance(max_expected, str):
        assert min_expected[0] <= min_time <= min_expected[1]
    else:
        assert min_time == min_expected
    if isinstance(max_expected, Sequence) and not isinstance(max_expected, str):
        assert max_expected[0] <= max_time <= max_expected[1]
    else:
        assert max_time == max_expected


@pytest.mark.parametrize(
    "time_s,curve,min_expected,max_expected", _TEST_DATA_TIME_TO_CURRENT
)
def test_get_current_from_time(
    time_s,
    curve: Literal["B", "C"],
    min_expected: int | float | Sequence[int | float],
    max_expected: int | float | Sequence[int | float],
):
    min_current, max_current = IEC60898.get_current_from_time(time_s, curve)
    if isinstance(min_expected, Sequence) and not isinstance(max_expected, str):
        assert min_expected[0] <= min_current <= min_expected[1]
    else:
        assert min_current == pytest.approx(min_expected, abs=0.1)
    if isinstance(max_expected, Sequence) and not isinstance(max_expected, str):
        assert max_expected[0] <= max_current <= max_expected[1]
    else:
        assert max_current == pytest.approx(max_expected, abs=0.1)
