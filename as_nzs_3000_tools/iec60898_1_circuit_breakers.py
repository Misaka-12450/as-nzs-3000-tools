from __future__ import annotations

import math
import textwrap
from functools import lru_cache
from io import StringIO
from typing import Literal, TypeAlias

import numpy as np
import pandas as pd

TIME_COLUMN: str = "time"
CURRENT_COLUMN: str = "current_multiple"

TripCurveType: TypeAlias = Literal["B", "C", "D"]
MinMaxType: TypeAlias = Literal["MIN", "MAX", "BOTH"]

_1_HR: int = 3600
TRIP_CURRENT_1_HR: tuple[float, float] = (1.13, 1.45)


class IEC60898Part1CircuitBreaker:
    """
    Base class for circuit breakers.

    :cvar MIN_CURVE: DataFrame containing the minimum trip curve (fastest trip).
    :cvar MAX_CURVE: DataFrame containing the maximum trip curve (slowest trip).
    :cvar TRIP_CURRENT_INSTANT: Dictionary mapping trip curve types to their
        instant trip current multiples.
    :cvar RATINGS_AVAILABLE: Tuple of available ratings for the circuit breaker.
    """

    MIN_CURVE: pd.DataFrame
    MAX_CURVE: pd.DataFrame

    TRIP_CURRENT_INSTANT: dict[str, tuple[float, float]] = {
        "B": (3, 5),
        "C": (5, 10),
        "D": (10, 20),
    }

    RATINGS_AVAILABLE: tuple[int, ...] = (2, 4, 6, 10, 16, 20, 25, 32, 40, 50, 63)

    @staticmethod
    def _interpolate_curve(
        curve: pd.DataFrame, col_x: str, col_y: str, x: float
    ) -> float:
        """
        Interpolate on a log-log curve. Returns NaN if x is out of range.

        :param curve: DataFrame containing the curve data.
        :param col_x: Name of the column to use as x values.
        :param col_y: Name of the column to use as y values.
        :param x: The x value to interpolate.
        :return: Interpolated y value.
        """
        xs = curve[col_x].values
        ys = curve[col_y].values
        if x < xs.min() or x > xs.max():
            return float("nan")
        # np.interp requires x to be sorted; sort both arrays together
        order = np.argsort(xs)
        log_x = np.log10(xs[order])
        log_y = np.log10(ys[order])
        return float(10 ** np.interp(math.log10(x), log_x, log_y))

    @classmethod
    @lru_cache(maxsize=None)
    def curve_interpolated(
        cls, curve_type: TripCurveType | None = None
    ) -> pd.DataFrame:
        """
        Get the interpolated full trip curve for the circuit breaker.

        :param curve_type: Type of trip curve. Use `None` to get the full curve range.
            # TODO: Implement filtering
        :return: DataFrame containing the interpolated curve in the format:
            | current_multiple | min_time | max_time |
        """

        x_min = min(
            cls.MIN_CURVE[CURRENT_COLUMN].min(), cls.MAX_CURVE[CURRENT_COLUMN].min()
        )
        x_max = max(
            cls.MIN_CURVE[CURRENT_COLUMN].max(), cls.MAX_CURVE[CURRENT_COLUMN].max()
        )

        # Sample many points on a log-spaced grid between min and max current multiples
        x_samples = np.round(np.logspace(np.log10(x_min), np.log10(x_max), 400), 2)
        y_samples_min = []
        y_samples_max = []

        for x in x_samples:
            y_samples_min.append(
                round(
                    cls._interpolate_curve(
                        cls.MIN_CURVE, CURRENT_COLUMN, TIME_COLUMN, x
                    ),
                    2,
                )
            )
            y_samples_max.append(
                round(
                    cls._interpolate_curve(
                        cls.MAX_CURVE, CURRENT_COLUMN, TIME_COLUMN, x
                    ),
                    2,
                )
            )

        return pd.DataFrame(
            {
                CURRENT_COLUMN: x_samples,
                "min_" + TIME_COLUMN: y_samples_min,
                "max_" + TIME_COLUMN: y_samples_max,
            }
        )

    @classmethod
    def _validate_curve(cls, curve: TripCurveType) -> None:
        if curve not in cls.TRIP_CURRENT_INSTANT:
            raise ValueError(
                f"Curve '{curve}' is not available for this circuit breaker. "
                f"Available curves: {tuple(cls.TRIP_CURRENT_INSTANT.keys())}"
            )

    @classmethod
    def get_trip_time(
        cls,
        current_multiple: float,
        curve: TripCurveType | None = None,
        min_max: MinMaxType = "BOTH",
    ) -> tuple[float, float]:
        """
        Calculate the trip time range for a given current multiple.

        :param current_multiple: Current multiple (I/In)
        :param curve: Type of trip curve
        :return: Tuple of (min, max) time in seconds up to 3600s
        """
        cls._validate_curve(curve)

        if current_multiple < cls.MIN_CURVE[CURRENT_COLUMN].min():
            # No trip within 1 hour
            return _1_HR, _1_HR

        if current_multiple < cls.MAX_CURVE[CURRENT_COLUMN].min():
            # Maximum trip time is more than 1 hour
            t_max = _1_HR
        else:
            # Calculate maximum trip time
            t_max = cls._interpolate_curve(
                cls.MIN_CURVE, CURRENT_COLUMN, TIME_COLUMN, current_multiple
            )

        if current_multiple > max(cls.TRIP_CURRENT_INSTANT[curve]):
            # Instant trip
            return 0, 0
        elif current_multiple > min(cls.TRIP_CURRENT_INSTANT[curve]):
            # Minimum trip time is instant
            t_min = 0
        else:
            # Calculate minimum trip time
            t_min = cls._interpolate_curve(
                cls.MAX_CURVE, CURRENT_COLUMN, TIME_COLUMN, current_multiple
            )

        return round(t_min, 1), round(t_max, 1)

    @classmethod
    def get_trip_current(cls, time: float, curve: TripCurveType) -> tuple[float, float]:
        """
        Calculate the trip current range for a given time.

        :param time: Time in seconds
        :param curve: Type of trip curve
        :return: Tuple of (min, max) current multiples (I/In), 2 decimal places.
            Multiply by the circuit breaker rated current to obtain amperes.
        """
        cls._validate_curve(curve)

        if time > _1_HR:
            # No trip within 1 hour
            return math.inf, math.inf

        if time <= 0:
            # Instant trip
            return min(cls.TRIP_CURRENT_INSTANT[curve]), max(
                cls.TRIP_CURRENT_INSTANT[curve]
            )

        # Calculate maximum and minimum trip current
        i_max = cls._interpolate_curve(cls.MIN_CURVE, TIME_COLUMN, CURRENT_COLUMN, time)
        i_min = cls._interpolate_curve(cls.MAX_CURVE, TIME_COLUMN, CURRENT_COLUMN, time)

        max_instant_i = max(cls.TRIP_CURRENT_INSTANT[curve])
        min_instant_i = min(cls.TRIP_CURRENT_INSTANT[curve])

        # Ensure trip current does not exceed instant trip values
        if math.isnan(i_max) or i_max > max_instant_i:
            i_max = max_instant_i

        if math.isnan(i_min) or i_min > min_instant_i:
            i_min = min_instant_i

        return round(i_min, 2), round(i_max, 2)

    def __init__(self, rating: int, curve: TripCurveType = "B"):
        """
        Initialise the circuit breaker with a given rating

        :param rating: Rating of the circuit breaker in amps
        :raises ValueError: If the rating is not in the `cls.RATINGS_AVAILABLE` tuple
        """
        self._validate_curve(curve)
        if rating in self.RATINGS_AVAILABLE:
            self.rating = rating
        else:
            raise ValueError(
                f"Rating {rating}A is not available for this circuit breaker. "
                f"Available ratings: {self.RATINGS_AVAILABLE}"
            )
        self.curve = curve

    @property
    def get_minimum_trip_current_amps(self) -> float:
        """
        Get the minimum current that will trip the circuit breaker

        :return: Trip current in amps
        """
        return self.rating * min(self.get_trip_current(3600, self.curve))


class IEC61009RCBO(IEC60898Part1CircuitBreaker):
    pass


class ClipsalMAX9RCBO(IEC61009RCBO):
    MIN_CURVE = pd.read_csv(
        StringIO(
            textwrap.dedent(
                """
                1.42,4000
                1.43,3000
                1.45,2000
                1.49,1000
                1.50,900
                1.51,800
                1.52,700
                1.53,600
                1.55,500
                1.58,400
                1.62,300
                1.69,200
                1.89,100
                1.93,90
                1.97,80
                2.00,75
                2.03,70
                2.11,60
                2.21,50
                2.36,40
                2.60,30
                3.00,21
                3.07,20
                4.00,12
                4.46,10
                4.80,9
                5.00,8.5
                5.28,8
                6.00,7
                7.00,6
                8.00,5
                9.00,4.5
                10.00,4
                14.00,3
                """
            ).strip()
        ),
        skipinitialspace=True,
        header=None,
        names=[CURRENT_COLUMN, TIME_COLUMN],
    )

    MAX_CURVE = pd.read_csv(
        StringIO(
            textwrap.dedent(
                """
                1.16,4000
                1.16,3000
                1.18,2000
                1.20,1000
                1.20,900
                1.21,800
                1.21,700
                1.22,600
                1.23,500
                1.24,400
                1.25,300
                1.28,200
                1.35,100
                1.37,90
                1.38,80
                1.40,70
                1.43,60
                1.46,50
                1.49,40
                1.56,30
                1.68,20
                1.96,10
                2.02,9
                2.08,8
                2.17,7
                2.27,6
                2.41,5
                2.63,4
                2.94,3
                3.00,2.9
                5.00,1.2
                5.75,1
                6.40,0.8
                10.00,0.5
                """
            ).strip()
        ),
        skipinitialspace=True,
        header=None,
        names=[CURRENT_COLUMN, TIME_COLUMN],
    )

    TRIP_CURRENT_INSTANT: dict[str, float] = {
        "B": (3.2, 4.8),
        "C": (6.4, 9.6),
        "D": (10, 14),
    }

    RATINGS_AVAILABLE = (6, 10, 16, 20, 25, 32, 40)

    def __init__(self, rating: int, curve: TripCurveType = "C"):
        """
        Initialise the circuit breaker with a given rating

        :param rating: Rating of the circuit breaker in amps
        :param curve: Trip curve type (default "C")
        :raises ValueError: If the rating is not in the `cls.RATINGS_AVAILABLE` tuple
        """
        super().__init__(rating, curve)


class LSBKNCircuitBreaker(IEC60898Part1CircuitBreaker):
    MIN_CURVE = pd.read_csv(
        StringIO(
            textwrap.dedent(
                """
                1.16, 3600
                1.18, 2400
                1.22, 1200
                1.26, 600
                1.28, 480
                1.30, 360
                1.34, 240
                1.41, 120
                1.50, 60
                1.55, 40
                1.72, 20
                1.93, 10
                2.00, 8
                2.13, 6
                2.36, 4
                3.00, 2
                """
            ).strip()
        ),
        skipinitialspace=True,
        header=None,
        names=[CURRENT_COLUMN, TIME_COLUMN],
    )

    MAX_CURVE = pd.read_csv(
        StringIO(
            textwrap.dedent(
                """
                1.48, 3600
                1.52, 2400
                1.58, 1200
                1.68, 600
                1.72, 480
                1.78, 360
                1.89, 240
                2.09, 120
                2.36, 60
                2.12, 120
                2.39, 60
                2.63, 40
                3.07, 20
                """
            ).strip()
        ),
        skipinitialspace=True,
        header=None,
        names=[CURRENT_COLUMN, TIME_COLUMN],
    )


__all__ = [
    "IEC60898Part1CircuitBreaker",
    "IEC61009RCBO",
    "ClipsalMAX9RCBO",
    "CURRENT_COLUMN",
    "TIME_COLUMN",
]
