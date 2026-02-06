import textwrap
from io import StringIO
from typing import Literal

import numpy as np
import pandas as pd

_MAX_B: pd.DataFrame = pd.read_csv(
    StringIO(
        textwrap.dedent(
            """
            1.25, 4008.09
            1.26, 2999.05
            1.27, 1981.68
            1.31, 991.37
            1.31, 888.53
            1.32, 796.35
            1.33, 688.83
            1.34, 595.81
            1.36, 494.43
            1.38, 397.15
            1.41, 298.00
            1.48, 198.02
            1.62, 98.13
            1.65, 87.94
            1.68, 78.11
            1.71, 69.58
            1.73, 66.16
            1.78, 58.41
            1.85, 48.46
            2.00, 35.50
            2.08, 29.62
            2.40, 19.84
            2.68, 14.53
            3.00, 11.56
            4.00, 6.53
            4.80, 5.00
            """
        )
    ),
    header=None,
    names=["current_multiplier", "time_s"],
    skipinitialspace=True,
)

_MIN_B: pd.DataFrame = pd.read_csv(
    StringIO(
        textwrap.dedent(
            """
            1.08, 4013.62
            1.08, 2941.72
            1.09, 1984.63
            1.10, 995.96
            1.10, 884.77
            1.10, 797.72
            1.10, 694.15
            1.10, 584.67
            1.11, 495.37
            1.12, 394.42
            1.12, 301.30
            1.14, 199.09
            1.18, 98.42
            1.19, 88.73
            1.20, 78.36
            1.20, 69.20
            1.22, 58.97
            1.24, 49.37
            1.26, 39.19
            1.29, 29.58
            1.36, 19.71
            1.52, 9.85
            1.55, 8.70
            1.59, 7.84
            1.63, 6.78
            1.70, 5.87
            1.80, 4.81
            1.90, 3.88
            1.99, 3.31
            2.10, 2.88
            2.50, 1.92
            2.99, 1.31
            3.19, 1.14
            """
        )
    ),
    header=None,
    names=["current_multiplier", "time_s"],
    skipinitialspace=True,
)

_MAX_C: pd.DataFrame = pd.read_csv(
    StringIO(
        textwrap.dedent(
            """
            4.79, 5.04
            5.00, 4.79
            6.00, 3.85
            7.01, 3.23
            8.00, 2.76
            9.00, 2.43
            9.60, 2.27
            """
        )
    ),
    header=None,
    names=["current_multiplier", "time_s"],
    skipinitialspace=True,
)

_MIN_C: pd.DataFrame = pd.read_csv(
    StringIO(
        textwrap.dedent(
            """
            4.79, 0.65
            5.01, 0.61
            6.00, 0.50
            6.39, 0.46
            """
        )
    ),
    header=None,
    names=["current_multiplier", "time_s"],
    skipinitialspace=True,
)


class IEC60898:
    @classmethod
    def _log_interp(
        cls, df: pd.DataFrame, num: float, axis: Literal["x", "y"]
    ) -> float:
        log_x = np.log(df["current_multiplier"].values)
        log_y = np.log(df["time_s"].values)
        k, v = (log_x, log_y) if axis == "x" else (log_y, log_x)
        order = np.argsort(k)
        k, v, l = k[order], v[order], np.log(num)

        if l >= k[-1]:
            return 0.0
        if l <= k[0]:
            slope = (v[1] - v[0]) / (k[1] - k[0])
            return float(np.exp(v[0] + slope * (l - k[0])))
        return float(np.exp(np.interp(l, k, v)))

    @classmethod
    def _get_curve_data(
        cls, curve: Literal["B", "C"] = "C"
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        if curve == "B":
            return _MIN_B, _MAX_B
        elif curve == "C":
            min_df = pd.concat([_MIN_B, _MIN_C], ignore_index=True)
            max_df = pd.concat([_MAX_B, _MAX_C], ignore_index=True)
            return min_df, max_df
        else:
            raise ValueError(f"Unknown curve type: {curve!r}")

    @classmethod
    def get_time_from_current(
        cls, i_ln: float, curve: Literal["B", "C"] = "C"
    ) -> tuple[float, float]:
        """Get the trip time for a given current and curve type.

        :param i_ln: The load current in multiples of the rated current.
        :param curve: The curve type ('B' or 'C').
        """

        min_df, max_df = cls._get_curve_data(curve)

        return cls._log_interp(min_df, i_ln, "x"), cls._log_interp(max_df, i_ln, "x")

    @classmethod
    def get_current_from_time(
        cls, time: float, curve: Literal["B", "C"] = "C"
    ) -> tuple[float, float]:
        """Get the current multiples for a given trip time and curve type.

        :param time: The trip time in seconds.
        :param curve: The curve type ('B' or 'C').
        """

        min_df, max_df = cls._get_curve_data(curve)

        min_current = min(
            cls._log_interp(min_df, time, "y"), min_df["current_multiplier"].max()
        )
        max_current = min(
            cls._log_interp(max_df, time, "y"), max_df["current_multiplier"].max()
        )

        return min_current, max_current
