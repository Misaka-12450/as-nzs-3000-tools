import math
from typing import Sequence

import pytest

from as_nzs_3000.iec60898_1_circuit_breakers import ClipsalMAX9RCBO as Max9
from as_nzs_3000.iec60898_1_circuit_breakers import TripCurveType

_TEST_CIRCUIT_BREAKERS = [Max9]  # TODO: Map breakers to test data when more are added

# MAX9
_TEST_DATA_CURRENT_TO_TIME = [
    (2, "B", 9, 75),
    (2, "C", 9, 75),
    (3, "B", 3, 20),
    (3, "C", 3, 20),
    (4, "B", 0, 15),
    (4, "C", 1.5, 15),
    (5, "B", 0, 0),
    (5, "C", 1, 8.5),
    (6, "C", 0.95, 7),
    (7, "C", 0, 6),
    (8, "C", 0, 5),
    (9, "C", 0, 4.5),
    (10, "C", 0, 0),
]

# MAX9
_TEST_DATA_TIME_TO_CURRENT = [
    (0, "B", 3.2, 4.8),
    (0, "C", 6.4, 9.6),
    (0, "D", 10, 14),
    (1, "B", 3.2, 4.8),
    (1, "C", 5.5, 9.6),
    (2, "B", 3.2, 4.8),
    (2, "C", 3.5, 9.6),
    (3, "B", 3, 4.8),
    (3, "C", 3, 9.6),
    (10, "C", 2, 4.5),
    (100, "C", 1.5, 2),
    (1000, "C", 1, 1.5),
]


def get_error_margin(value: float, margin_multiplier=0.5) -> float:
    """
    Calculate an error margin based on the magnitude of the value

    :param value: The value to calculate the margin for
    :param margin_multiplier: The multiplier to apply to the order of magnitude
    :return: The calculated error margin
    """
    if value == 0:
        return margin_multiplier  # Default small margin for zero
    return margin_multiplier * 10 ** math.floor(math.log10(abs(value)))


@pytest.mark.parametrize("cb", _TEST_CIRCUIT_BREAKERS)
@pytest.mark.parametrize(
    "i_ln,curve,min_expected,max_expected", _TEST_DATA_CURRENT_TO_TIME
)
def test_get_trip_time(
    cb,
    i_ln,
    curve: TripCurveType,
    min_expected: int | float | Sequence[int | float],
    max_expected: int | float | Sequence[int | float],
):
    """
    Test `IEC60898Part1CircuitBreaker.get_trip_time()`

    :param cb: Circuit breaker class
    :param i_ln: Multiplier of rated current
    :param curve: Trip curve type
    :param min_expected: Minimum expected trip time
    :param max_expected: Maximum expected trip time
    :return:
    """
    min_time, max_time = cb.get_trip_time(i_ln, curve)
    if isinstance(min_expected, Sequence) and not isinstance(max_expected, str):
        assert min_expected[0] <= min_time <= min_expected[1]
    else:
        assert min_time == pytest.approx(
            min_expected, abs=get_error_margin(min_expected)
        )

    if isinstance(max_expected, Sequence) and not isinstance(max_expected, str):
        assert max_expected[0] <= max_time <= max_expected[1]
    else:
        assert max_time == pytest.approx(
            max_expected, abs=get_error_margin(max_expected)
        )


@pytest.mark.parametrize("cb", _TEST_CIRCUIT_BREAKERS)
@pytest.mark.parametrize(
    "time_s,curve,min_expected,max_expected", _TEST_DATA_TIME_TO_CURRENT
)
def test_get_trip_current(
    cb,
    time_s,
    curve: TripCurveType,
    min_expected: int | float | Sequence[int | float],
    max_expected: int | float | Sequence[int | float],
):
    """
    Test `IEC60898Part1CircuitBreaker.get_trip_current()`

    :param cb: Circuit breaker class
    :param time_s: Time in seconds
    :param curve: Trip curve type
    :param min_expected: Minimum expected trip current
    :param max_expected: Maximum expected trip current
    :return:
    """
    min_current, max_current = cb.get_trip_current(time_s, curve)
    if isinstance(min_expected, Sequence) and not isinstance(max_expected, str):
        assert min_expected[0] <= min_current <= min_expected[1]
    else:
        assert min_current == pytest.approx(
            min_expected, abs=get_error_margin(min_expected)
        )
    if isinstance(max_expected, Sequence) and not isinstance(max_expected, str):
        assert max_expected[0] <= max_current <= max_expected[1]
    else:
        assert max_current == pytest.approx(
            max_expected, abs=get_error_margin(max_expected)
        )
