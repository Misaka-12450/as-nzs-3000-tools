from __future__ import annotations

from typing import Iterable, Literal

import roman

from as_nzs_3000_tools import as_nzs_3000_c1_notes as c1_notes
from as_nzs_3000_tools.common import NOMINAL_VOLTAGE


class IncorrectLoadGroupException(Exception):
    def __init__(self, correct_group: type[LoadGroup], reason: str = ""):
        self.correct_group = correct_group
        msg = f"Use {repr(correct_group)} ({correct_group.__name__}) instead."
        if reason:
            msg = f"{reason} {msg}"
        super().__init__(msg)


class LoadGroupNotApplicableException(Exception):
    def __init__(self, load_group: type[LoadGroup], num: int = 1):
        self.load_group = load_group
        msg = (
            f"{repr(load_group)} ({load_group.__name__}) "
            f"is not applicable to {num} {"unit" if num==1 else "units"}."
        )
        super().__init__(msg)


class _LoadGroupMeta(type):
    def __repr__(cls) -> str:
        if not cls.code:
            return ""
        parts = [
            f"({roman.toRoman(part).lower() if isinstance(part, int) else str(part)})"
            for part in cls.code
        ]
        return " ".join(parts)

    def __str__(cls) -> str:
        # TODO: #4 Deprecate
        s: str = ""

        if cls.exceptions:
            s = cls._add_strings(s, "**Exceptions**")
            for excepted_load_group in cls.exceptions:
                s = cls._add_strings(
                    s, f"{repr(excepted_load_group)} {excepted_load_group.description}"
                )

        if cls.notes:
            s = cls._add_strings(s, "**Notes**")
            for note in cls.notes:
                s = cls._add_strings(s, str(note))

        return s

    def is_num_living_units_applicable(cls, num: int) -> bool:
        """
        Check if the number of living units is applicable for this load group.
        :param num: Number of living units.
        :return: True if applicable, False otherwise.
        """
        if cls._min_num_units and num < cls._min_num_units:
            return False
        return True


class LoadGroup(metaclass=_LoadGroupMeta):
    #: Load group number in list representation. E.g. ['a', 1] for load group (a) (i).
    code: list[str | int] = []

    #: Short title of the load group.
    title: str = ""

    #: Description of the load group.
    description: str = ""

    #: Loads in other load groups and excluded from this load group.
    exceptions: list[type[LoadGroup]] = []

    #: Notes applicable to the load group.
    notes: list[type[c1_notes.C1Note]] = []

    #: Minimum number of living units required for this load group.
    _min_num_units: int = 1

    #: Number of loads in this load group.
    num_loads: int

    def __repr__(self) -> str:
        return repr(self.__class__)

    def __str__(self) -> str:
        return str(self.__class__)

    def __init__(self, num_living_units: int = 1):
        """
        Class for calculating maximum demand for various load types.
        Based on AS/NZS 3000 Table C1.

        :param int num_living_units: Number of living units per phase.
            Use 1 for single domestic installations.

        :raises ValueError: If any value is zero or negative.
        :raises IncorrectLoadGroupException:
            If the load should be in another load group.
        :raises LoadGroupNotApplicableException: If the load group is not applicable.
        """

        if num_living_units < self._min_num_units:
            raise LoadGroupNotApplicableException(self.__class__, num_living_units)

        self.num_living_units = num_living_units

    @staticmethod
    def _add_strings(s1: str, s2: str, n: int = 2) -> str:
        """
        Add two strings together, and newline characters in-between if both strings are
        not empty.
        :return: The combined string with newline(s) in-between if applicable.
        """
        # TODO: #4 Deprecate
        if s1 and s2:
            return s1 + "\n" * n + s2
        return s1 + s2

    @property
    def total_rating_a(self) -> float:
        """Total load in amperes."""
        raise NotImplementedError

    def _calculate_maximum_demand_a(self) -> float:
        """
        Fallback maximum demand calculation used by all tier methods.
        Subclasses with one formula for all tiers override this method.
        :return: Maximum demand in amperes.
        """
        raise NotImplementedError

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        """
        Calculate maximum demand for single unit installations.
        :return: Maximum demand in amperes.
        """
        return self._calculate_maximum_demand_a()

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        """
        Calculate maximum demand for installations with 2 to 5 living units.
        :return: Maximum demand in amperes.
        """
        return self._calculate_maximum_demand_a()

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        """
        Calculate maximum demand for installations with 6 to 20 living units.
        :return: Maximum demand in amperes.
        """
        return self._calculate_maximum_demand_a()

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        """
        Calculate maximum demand for installations with more than 20 living units.
        :return: Maximum demand in amperes.
        """
        return self._calculate_maximum_demand_a()

    @property
    def maximum_demand_a(self) -> float:
        """
        Calculates maximum demand of the load group in amperes.
        :return: Maximum demand in amperes.
        """
        if self.num_living_units == 1:
            return self._calculate_maximum_demand_a_1_living_unit()
        elif 2 <= self.num_living_units <= 5:
            return self._calculate_maximum_demand_a_2_to_5_living_units()
        elif 6 <= self.num_living_units <= 20:
            return self._calculate_maximum_demand_a_6_to_20_living_units()
        else:  # self.num_living_units > 20
            return self._calculate_maximum_demand_a_21_plus_living_units()

    @property
    def maximum_demand_w(self) -> float:
        """
        Calculates maximum demand of the load group in watts.
        :return: Maximum demand in watts.
        """
        return self.maximum_demand_a * NOMINAL_VOLTAGE

    @classmethod
    def get_exceptions(cls) -> str:
        """
        Get exceptions as a formatted string.
        :return: Exceptions as a string.
        """
        if not cls.exceptions:
            return ""

        s: str = ""
        for excepted_load_group in cls.exceptions:
            s = cls._add_strings(
                s, f"{repr(excepted_load_group)} {excepted_load_group.description}"
            )
        return s


class LoadGroupRatingBased(LoadGroup):
    def __init__(
        self,
        rating: float | Iterable[float],
        rating_unit: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        """
        Load group whose maximum demand is calculated based on the rating of the loads.

        :param rating: Rating of the load. Can be a single value or an iterable
            (e.g. list) of values.
        :param rating_unit: Unit of the rating, either "A" for amperes or "W" for watts.
        :param num_living_units: Number of living units.
        :raises ValueError: If the rating is not valid.
        """
        super().__init__(num_living_units=num_living_units)

        if isinstance(rating, Iterable) and not isinstance(rating, str):
            ratings = list(rating)
        else:
            ratings = [rating]

        for r in ratings:
            if not isinstance(r, (int, float)) or r < 0:
                raise ValueError(
                    "All rating values must be a number no less than zero."
                )

        if rating_unit != "A" and rating_unit != "W":
            raise ValueError("rating_unit must be either 'A' or 'W'.")

        if rating_unit == "W":
            ratings = self.watts_to_amperes(ratings)

        self.ratings = ratings

    @staticmethod
    def watts_to_amperes(rating_w: float | Iterable[float]) -> float | list[float]:
        """
        Convert rating in watts to amperes.
        :param rating_w: Rating in watts. Can be a single value or an iterable (e.g. list) of values.
        :return: Ratings in amperes.
        """
        if isinstance(rating_w, Iterable) and not isinstance(rating_w, str):
            ratings_w = list(rating_w)
        else:
            return rating_w / NOMINAL_VOLTAGE

        ratings_a = []
        for r in ratings_w:
            if not isinstance(r, (int, float)) or r < 0:
                raise ValueError(
                    "All rating values must be a number no less than zero."
                )
            ratings_a.append(r / NOMINAL_VOLTAGE)

        return ratings_a

    @property
    def num_loads(self) -> int:
        """Number of loads."""
        return len(self.ratings)

    @property
    def total_rating_a(self) -> float:
        """Total load in amperes."""
        return sum(self.ratings)

    def add(self, rating: float) -> None:
        """
        Adds a load to the load group.

        :param rating: The rating of the load to be added.
        """

        self.ratings.append(rating)

    def change(self, old_rating: float, new_rating: float) -> None:
        """
        Change the rating of a load in the load group. The old rating value is replaced with the new one.

        :param old_rating: The old rating value to be replaced.
        :param new_rating: The new rating value to replace the old one.
        """
        if not old_rating in self.ratings:
            raise ValueError("Old rating not found.")

        self.ratings[self.ratings.index(old_rating)] = new_rating

    def remove(self, rating: float, num: int = 1) -> None:
        """
        Remove a load from the load group.

        :param rating: The rating of the load to be removed.
        :param num: The number of loads with the specified rating to be removed. Default is 1.
        """
        if not self.ratings.count(rating) >= num:
            raise ValueError("Not enough ratings found.")

        for i in range(self.num_loads - 1, -1, -1):
            if self.ratings[i] == rating:
                del self.ratings[i]
                num -= 1
                if num == 0:
                    break


class LoadGroupPointBased(LoadGroup):
    max_rating: float

    def __init__(self, num_loads: int = 1, num_living_units: int = 1):
        """
        Load group whose maximum demand is calculated based on the number of loads (points).

        :param num_loads: Number of loads (points).
        :param num_living_units: Number of living units.
        :raises ValueError: If num_loads is not greater than zero.
        """

        if num_loads < 1:
            raise ValueError("num_load must be greater than zero.")

        super().__init__(num_living_units)
        self.num_loads = num_loads

    @property
    def total_rating_a(self) -> float:
        """Total load in amperes."""
        return self.num_loads * self.max_rating


class LoadGroupManual(LoadGroupRatingBased):
    title = "Manually assessed maximum demand"

    def _calculate_maximum_demand_a(self) -> float:
        return self.total_rating_a


class LoadGroupA1(LoadGroupPointBased):
    code = ["a", 1]
    title = "Lighting"
    description = "Lighting except (ii) and load group (h) below"
    notes = [c1_notes.C1Note4, c1_notes.C1Note6]

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 3 A for 1 to 20 points + 2 A for each additional 20 points or part thereof
        if self.num_loads <= 20:
            return 3
        return 3 + 2 * ((self.num_loads - 1) // 20)

    def _calculate_maximum_demand_a_2_to_5_living_units(self):
        # 6 A
        return 6

    def _calculate_maximum_demand_a_6_to_20_living_units(self):
        # 5 A + 0.25A per living unit
        return 5 + 0.25 * self.num_living_units

    def _calculate_maximum_demand_a_21_plus_living_units(self):
        # 0.5A per living unit
        return 0.5 * self.num_living_units


class LoadGroupA2(LoadGroupPointBased):
    code = ["a", 2]
    title = "Outdoor lighting"
    description = "Outdoor lighting exceeding a total of 1000 W"
    notes = [c1_notes.C1Note6, c1_notes.C1Note7]

    def _calculate_maximum_demand_a(self) -> float:
        # No assessment for the purpose of maximum demand
        return 0.0

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 75% connected load
        return self.total_rating_a * 0.75


class LoadGroupB1(LoadGroupPointBased):
    code = ["b", 1]
    title = "Socket-outlets <= 10 A"
    description = (
        "Socket-outlets not exceeding 10 A. Permanently "
        "connected electrical equipment not exceeding 10 A "
        "and not included in other load groups"
    )
    notes = [c1_notes.C1Note5, c1_notes.C1Note8, c1_notes.C1Note9]

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 10 A for 1 to 20 points + 5 A for each additional 20 points or part thereof
        if self.num_loads <= 20:
            return 10
        return 10 + 5 * ((self.num_loads - 1) // 20)

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        # 10 A + 5 A per living unit
        return 10 + 5 * self.num_living_units

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        # 15 A + 3.75 A per living unit
        return 15 + 3.75 * self.num_living_units

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        # 50 A + 1.9 A per living unit
        return 50 + 1.9 * self.num_living_units


class LoadGroupB2(LoadGroupPointBased):
    code = ["b", 2]
    title = "Socket-outlets 15 A"
    description = (
        "Where the electrical installation includes one or "
        "more 15 A socket-outlets, other than socket-outlets "
        "provided to supply electrical equipment set out in "
        "load groups (c), (d), (e), (f), (g) and (l)"
    )
    notes = [c1_notes.C1Note8, c1_notes.C1Note10]

    def __init__(
        self,
        rating: float | list[float] | None = None,
        num_load: int = 1,
        rating_type: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        super().__init__(rating, num_load, rating_type, num_living_units)

    def _calculate_maximum_demand_a(self) -> float:
        # 10 A
        return 10


class LoadGroupB3(LoadGroupPointBased):
    code = ["b", 3]
    title = "Socket-outlets 20 A"
    description = (
        "Where the electrical installation includes one or "
        "more 20 A socket-outlets, other than socket-outlets "
        "provided to supply electrical equipment set out in "
        "load groups (c), (d), (e), (f), (g) and (l)"
    )
    notes = [c1_notes.C1Note8, c1_notes.C1Note10]

    def _calculate_maximum_demand_a(self) -> float:
        # 15 A
        return 15


class LoadGroupC(LoadGroupRatingBased):
    code = ["c"]
    title = "Ranges, cooking appliances, laundry equipment > 10 A"
    description = """
        Ranges, cooking appliances, laundry equipment or
        socket-outlets rated at more than 10 A for the
        connection thereof
        """
    notes = [c1_notes.C1Note8]

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 50% connected load
        return self.total_rating_a * 0.5

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        # 15 A
        return 15

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        # 2.8 A per living unit
        return 2.8 * self.num_living_units

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        # 2.8 A per living unit
        return 2.8 * self.num_living_units


class LoadGroupD(LoadGroupRatingBased):
    """
    Fixed space heating or airconditioning equipment,
    saunas or socket-outlets rated at more than 10 A for the
    connection thereof(8, 11)
    """

    code = ["d"]
    title = "Fixed space heating or airconditioning equipment, saunas > 10 A"
    description = (
        "Fixed space heating or airconditioning equipment, "
        "saunas or socket-outlets rated at more than 10 A for the "
        "connection thereof"
    )
    notes = [c1_notes.C1Note8, c1_notes.C1Note11]

    def _calculate_maximum_demand_a(self) -> float:
        # 75% connected load
        return self.total_rating_a * 0.75


class LoadGroupE(LoadGroupRatingBased):
    """
    Instantaneous water heaters(12)
    """

    code = ["e"]
    title = "Instantaneous water heaters"
    description = title
    notes = [c1_notes.C1Note12]

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 33.3% connected load
        return self.total_rating_a * 0.33

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        # 6 A per living unit
        return 6 * self.num_living_units

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        # 6 A per living unit
        return 6 * self.num_living_units

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        # 100 A + 0.8 A per living unit
        return 100 + 0.8 * self.num_living_units


class LoadGroupF(LoadGroupRatingBased):
    """
    Storage water heaters(13)
    """

    code = ["f"]
    title = "Storage water heaters"
    description = title
    notes = [c1_notes.C1Note13]

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # Full-load current
        return self.total_rating_a

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        # 6 A per living unit
        return 6 * self.num_living_units

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        # 6 A per living unit
        return 6 * self.num_living_units

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        # 100 A + 0.8 A per living unit
        return 100 + 0.8 * self.num_living_units


class LoadGroupG(LoadGroupRatingBased):
    """
    Spa and swimming pool heaters
    """

    code = ["g"]
    title = "Spa and swimming pool heaters"
    description = title
    notes = [c1_notes.C1Note14]

    def __init__(self, rating=None, num_load=1, rating_type="A", num_living_units=1):
        super().__init__(rating, num_load, rating_type, num_living_units)
        raise NotImplementedError(
            "This load group is currently not supported."
        )  # FIXME #6

        # 75% of the largest spa, plus 75% of the largest swimming pool,
        # plus 25% of the remainder


class LoadGroupH(LoadGroupRatingBased):
    """
    Communal lighting
    """

    code = ["h"]
    title = "Communal lighting"
    description = title
    notes = [c1_notes.C1Note6, c1_notes.C1Note7]
    _min_num_units = 2

    def _calculate_maximum_demand_a(self) -> float:
        # Full connected load
        return self.total_rating_a


class LoadGroupI(LoadGroupPointBased):
    """
    Socket-outlets not included in load groups (j) and (m)
    below(8, 10, 14)
    Not applicable 2 A per point, up to a maximum of 15 A
    Permanently connected electrical equipment not
    exceeding 10 A
    """

    code = ["i"]
    title = "Socket-outlets and permanently connected electrical equipment <= 10 A"
    description = (
        "Socket-outlets not included in load groups (j) and (m) "
        "below. Permanently connected electrical equipment not "
        "exceeding 10 A"
    )
    notes = [c1_notes.C1Note8, c1_notes.C1Note10, c1_notes.C1Note14]
    _min_num_units = 2

    def _calculate_maximum_demand_a(self) -> float:
        # 2 A per point, up to a maximum of 15 A
        return min(2 * self.num_loads, 15)


class LoadGroupJ1(LoadGroupRatingBased):
    """
    Appliances rated at more than 10 A and socket-outlets
    for the connection thereof
    Clothes dryers, water heaters, self-heating washing
    machines, wash boilers(8)
    """

    code = ["j", 1]
    title = "Clothes dryers, water heaters, self-heating washing machines, wash boilers > 10 A"
    description = (
        "Appliances rated at more than 10 A and socket-outlets "
        "for the connection thereof — "
        "Clothes dryers, water heaters, "
        "self-heating washing machines, wash boilers"
    )
    notes = [c1_notes.C1Note8]

    _min_num_units = 2

    def _calculate_maximum_demand_a(self) -> float:
        # 50% connected load
        return self.total_rating_a * 0.5


class LoadGroupJ2(LoadGroupRatingBased):
    code = ["j", 2]
    title = "Fixed space heating, airconditioning equipment, saunas > 10 A"
    description = (
        "Appliances rated at more than 10 A and socket-outlets "
        "for the connection thereof — "
        "Fixed space heating, airconditioning equipment, "
        "saunas"
    )
    notes = [c1_notes.C1Note11]

    _min_num_units = 2

    def _calculate_maximum_demand_a(self) -> float:
        # 75% connected load
        return self.total_rating_a * 0.75


class LoadGroupJ3(LoadGroupRatingBased):
    code = ["j", 3]
    title = "Spa and swimming pool heaters > 10 A"
    description = (
        "Appliances rated at more than 10 A and socket-outlets "
        "for the connection thereof — "
        "Spa and swimming pool heaters"
    )
    _min_num_units = 2

    def __init__(
        self,
        rating: float | list[float] | None = None,
        num_load: int = 1,
        rating_type: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        super().__init__(rating, num_load, rating_type, num_living_units)
        raise NotImplementedError(
            "This load group is currently not supported."
        )  # FIXME #6
        # 75% of the largest spa plus 75% of the largest swimming pool,
        # plus 25% of the remainder


class LoadGroupJ4(LoadGroupRatingBased):
    code = ["j", 4]
    title = "Charging equipment associated with electric vehicles"
    description = (
        "Appliances rated at more than 10 A and socket-outlets "
        "for the connection thereof — "
        "Charging equipment associated with electric vehicles"
    )

    def _calculate_maximum_demand_a_1_living_unit(self):
        # Fully connected load
        return self.total_rating_a

    def _calculate_maximum_demand_a_2_to_5_living_units(self):
        # 100% connected load
        return self.total_rating_a

    def _calculate_maximum_demand_a_6_to_20_living_units(self):
        # 90% connected load
        return self.total_rating_a * 0.9

    def _calculate_maximum_demand_a_21_plus_living_units(self):
        # 75% connected load
        return self.total_rating_a * 0.75


class LoadGroupK(LoadGroupRatingBased):
    code = ["k"]
    description = "Lifts"


class LoadGroupL(LoadGroupRatingBased):
    code = ["l"]
    description = "Motors"


class LoadGroupM(LoadGroupRatingBased):
    code = ["m"]
    title = "Appliances other than those set out in load groups (a) to (l) above"
    description = (
        "Appliances, including socket-outlets other than those set"
        "out in load groups (a) to (l) above, e.g. pottery kilns,"
        "welding machines, radio transmitters, X-ray equipment"
        "and the like"
    )

    def __init__(
        self,
        rating: float | Iterable[float] | None = None,
        rating_unit: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        if rating_unit == "W":
            rating = self.watts_to_amperes(rating)

        if (rating <= 5 and num_living_units == 1) or rating <= 10:
            super().__init__(0, "A", num_living_units)
        else:
            super().__init__(rating, "A", num_living_units)


_ALL_LOAD_GROUPS = [
    LoadGroupA1,
    LoadGroupA2,
    LoadGroupB1,
    LoadGroupB2,
    LoadGroupB3,
    LoadGroupC,
    LoadGroupD,
    LoadGroupE,
    LoadGroupF,
    LoadGroupG,
    LoadGroupH,
    LoadGroupI,
    LoadGroupJ1,
    LoadGroupJ2,
    LoadGroupJ3,
    LoadGroupJ4,
    LoadGroupK,
    LoadGroupL,
    LoadGroupM,
]

# Resolve forward references
LoadGroupA1.exceptions = [LoadGroupA2, LoadGroupH]
_LOAD_GROUP_B_EXCEPTIONS = [
    LoadGroupC,
    LoadGroupD,
    LoadGroupE,
    LoadGroupF,
    LoadGroupG,
    LoadGroupL,
]
LoadGroupB2.exceptions = _LOAD_GROUP_B_EXCEPTIONS
LoadGroupB3.exceptions = _LOAD_GROUP_B_EXCEPTIONS
LoadGroupI.exceptions = [LoadGroupJ1, LoadGroupJ2, LoadGroupJ3, LoadGroupJ4, LoadGroupL]
LoadGroupM.exceptions = [lg for lg in _ALL_LOAD_GROUPS if lg != LoadGroupM]


__all__ = [
    "LoadGroup",
    "IncorrectLoadGroupException",
    "LoadGroupNotApplicableException",
]
__all__ += [lg.__name__ for lg in _ALL_LOAD_GROUPS]
