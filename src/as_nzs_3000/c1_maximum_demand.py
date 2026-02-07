from __future__ import annotations

from typing import Literal

from as_nzs_3000 import c1_notes

_NOMINAL_VOLTAGE = 230


class IncorrectLoadGroupException(Exception):
    def __init__(self, correct_group: type[C1LoadGroup], reason: str = ""):
        self.correct_group = correct_group
        msg = f"Use {repr(correct_group)} ({correct_group.__name__}) instead."
        if reason:
            msg = f"{reason} {msg}"
        super().__init__(msg)


class LoadGroupNotApplicableException(Exception):
    def __init__(self, load_group: type[C1LoadGroup], num: int = 1):
        self.load_group = load_group
        msg = (
            f"{repr(load_group)} ({load_group.__name__}) "
            f"is not applicable to {num} {"unit" if num==1 else "units"}."
        )
        super().__init__(msg)


class _C1LoadGroupMeta(type):
    def __repr__(cls) -> str:
        if not cls.load_group:
            return cls.__name__
        parts = [
            f"({'i' * part if isinstance(part, int) else str(part)})"
            for part in cls.load_group
        ]
        return " ".join(parts)


class C1LoadGroup(metaclass=_C1LoadGroupMeta):
    #: Load group number in list representation. E.g. ['a', 1] for load group (a) (i).
    load_group: list[str | int] = []

    #: Description of the load group.
    load_group_description: str = ""

    #: Loads in other load groups and excluded from this load group.
    load_group_exception: list[type[C1LoadGroup]] = []

    #: Notes applicable to the load group.
    notes: list[type[c1_notes.C1Note]] = []

    def __init__(
        self,
        rating: float | list[float] | None = None,
        num_load: int = 1,
        rating_type: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        """
        Class for calculating maximum demand for various load types.
        Based on AS/NZS 3000 Table C1.

        :param float | list[float] rating: Rating per unit.
            Can be a list for different ratings.
        :param int num_load: Number of loads in this load group.
            If `rating` is a list, this is the number of loads per rating.
            E.g. `rating=[10, 20]` and `num_load=2` means 2 loads of 10 and 2 loads of
            20.
        :param Literal["A", "W"] rating_type:
            Type of rating, either "A" for amperes or "W" for watts.
        :param int num_living_units: Number of living units per phase.
            Use 1 for single domestic installations.

        :raises ValueError: If any value is zero or negative.
        :raises IncorrectLoadGroupException:
            If the load should be in another load group.
        :raises LoadGroupNotApplicableException: If the load group is not applicable.
        """

        # Validate ratings
        if rating is None:
            raise ValueError("rating must be provided.")
        ratings = rating if isinstance(rating, list) else [rating]
        for r in ratings:
            if r <= 0:
                raise ValueError("All rating values must be greater than zero.")

        # Convert ratings to amperes if necessary
        if rating_type == "A":
            self.rating_a = ratings
        elif rating_type == "W":
            self.rating_a = [r / _NOMINAL_VOLTAGE for r in ratings]
        else:
            raise ValueError("rating_type must be either 'A' or 'W'.")

        # Validate number of units
        if num_load <= 0:
            raise ValueError("num_load must be greater than zero.")
        if num_load > 1:
            self.rating_a = self.rating_a * num_load

        # Validate number of living units
        if num_living_units > 0:
            self.num_living_units = num_living_units
        else:
            raise ValueError("num_living_units must be greater than zero.")

    @staticmethod
    def _add_strings(s1: str, s2: str, n: int = 2) -> str:
        """
        Add two strings together, and newline characters in-between if both strings are
        not empty.
        :return: The combined string with newline(s) in-between if applicable.
        """
        if s1 and s2:
            return s1 + "\n" * n + s2
        return s1 + s2

    def __repr__(self) -> str:
        if not self.load_group:
            return self.__class__.__name__

        parts = [
            f"({'i' * part if isinstance(part, int) else str(part)})"
            for part in self.load_group
        ]
        return " ".join(parts)

    def __str__(self) -> str:
        s: str = ""
        if self.load_group_description:
            s += self.load_group_description

        if self.load_group_exception:
            s = self._add_strings(s, "Exceptions:")
            for exception in self.load_group_exception:
                s = self._add_strings(
                    s, f"{repr(exception)} {exception.load_group_description}"
                )

        if self.notes:
            s = self._add_strings(s, "Notes:")
            for note in self.notes:
                s = self._add_strings(s, str(note))

        return s

    @property
    def num_loads(self) -> int:
        """
        Get the number of loads in this load group.
        :return: The number of loads.
        """
        return len(self.rating_a)

    @property
    def rating_w(self) -> list[float]:
        """Rating per unit in watts."""
        return [r * _NOMINAL_VOLTAGE for r in self.rating_a]

    @staticmethod
    def _maximum_demand_not_assessed() -> float:
        """
        Load groups where maximum demand is not assessed.
        :return: Always returns 0.0 A.
        """
        return 0.0

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        """
        Calculate maximum demand for single unit installations.
        :return: Maximum demand in amperes.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        """
        Calculate maximum demand for installations with 2 to 5 living units.
        :return: Maximum demand in amperes.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        """
        Calculate maximum demand for installations with 6 to 20 living units.
        :return: Maximum demand in amperes.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        """
        Calculate maximum demand for installations with more than 20 living units.
        :return: Maximum demand in amperes.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

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
        return self.maximum_demand_a * _NOMINAL_VOLTAGE


class C1A1(C1LoadGroup):
    load_group = ["a", 1]
    load_group_description = "Lighting except (ii) and load group (h) below"
    notes = [c1_notes.C1Note4, c1_notes.C1Note6]

    def __init__(
        self,
        rating: float | list[float] | None = None,
        num_load: int = 1,
        rating_type: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        super().__init__(rating, num_load, rating_type, num_living_units)

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 3 A for 1 to 20 points + 2 A for each additional 20 points or part thereof
        if self.num_loads <= 20:
            return 3
        return 3 + 2 * (self.num_loads // 20)

    def _calculate_maximum_demand_a_2_to_5_living_units(self):
        # 6 A
        return 6

    def _calculate_maximum_demand_a_6_to_20_living_units(self):
        # 5 A + 0.25A per living unit
        return 5 + 0.25 * self.num_living_units

    def _calculate_maximum_demand_a_21_plus_living_units(self):
        # 0.5A per living unit
        return 0.5 * self.num_living_units


class C1A2(C1LoadGroup):
    load_group = ["a", 2]
    load_group_description = "Outdoor lighting exceeding a total of 1000 W"
    notes = [c1_notes.C1Note6, c1_notes.C1Note7]

    def __init__(
        self,
        rating: float | list[float] | None = None,
        num_load: int = 1,
        rating_type: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        super().__init__(rating, num_load, rating_type, num_living_units)
        if (sum_rating_w := sum(self.rating_w)) < 1000:
            raise IncorrectLoadGroupException(
                C1A1,
                (f"Total wattage ({sum_rating_w} W) does not exceed" " 1000 W."),
            )

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 75% connected load
        return sum(self.rating_a) * 0.75

    def _calculate_maximum_demand_a_2_to_5(self) -> float:
        # No assessment for the purpose of maximum demand
        return self._maximum_demand_not_assessed()

    def _calculate_maximum_demand_a_6_to_20(self) -> float:
        # No assessment for the purpose of maximum demand
        return self._maximum_demand_not_assessed()

    def _calculate_maximum_demand_a_21_plus(self) -> float:
        # No assessment for the purpose of maximum demand
        return self._maximum_demand_not_assessed()


class C1B1(C1LoadGroup):
    load_group = ["b", 1]
    load_group_description = (
        "Socket-outlets not exceeding 10 A. Permanently "
        "connected electrical equipment not exceeding 10 A "
        "and not included in other load groups"
    )
    notes = [c1_notes.C1Note5, c1_notes.C1Note8, c1_notes.C1Note9]

    def __init__(
        self,
        rating: float | list[float] | None = None,
        num_load: int = 1,
        rating_type: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        super().__init__(rating, num_load, rating_type, num_living_units)

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 10 A for 1 to 20 points + 5 A for each additional 20 points or part thereof
        if self.num_loads <= 20:
            return 10
        return 10 + 5 * (self.num_loads // 20)

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        # 10 A + 5 A per living unit
        return 10 + 5 * self.num_living_units

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        # 15 A + 3.75 A per living unit
        return 15 + 3.75 * self.num_living_units

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        # 50 A + 1.9 A per living unit
        return 50 + 1.9 * self.num_living_units


class C1B2(C1LoadGroup):
    load_group = ["b", 2]
    load_group_description = (
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

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 10 A
        return 10

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        # 10 A
        return 10

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        # 10 A
        return 10

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        # 10 A
        return 10


class C1B3(C1LoadGroup):
    load_group = ["b", 3]
    load_group_description = (
        "Where the electrical installation includes one or "
        "more 20 A socket-outlets, other than socket-outlets "
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

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 15 A
        return 15

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        # 15 A
        return 15

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        # 15 A
        return 15

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        # 15 A
        return 15


class C1C(C1LoadGroup):
    load_group = ["c"]
    load_group_description = """
        Ranges, cooking appliances, laundry equipment or
        socket-outlets rated at more than 10 A for the
        connection thereof
        """
    notes = [c1_notes.C1Note8]

    def __init__(
        self,
        rating: float | list[float] | None = None,
        num_load: int = 1,
        rating_type: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        super().__init__(rating, num_load, rating_type, num_living_units)

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 50% connected load
        return sum(self.rating_a) * 0.5

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        # 15 A
        return 15

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        # 2.8 A per living unit
        return 2.8 * self.num_living_units

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        # 2.8 A per living unit
        return 2.8 * self.num_living_units


class C1D(C1LoadGroup):
    """
    Fixed space heating or airconditioning equipment,
    saunas or socket-outlets rated at more than 10 A for the
    connection thereof(8, 11)
    """

    load_group = ["d"]
    load_group_description = (
        "Fixed space heating or airconditioning equipment, "
        "saunas or socket-outlets rated at more than 10 A for the "
        "connection thereof"
    )
    notes = [c1_notes.C1Note8, c1_notes.C1Note11]

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 75% connected load
        return sum(self.rating_a) * 0.75

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        # 75% connected load
        return sum(self.rating_a) * 0.75

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        # 75% connected load
        return sum(self.rating_a) * 0.75

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        # 75% connected load
        return sum(self.rating_a) * 0.75


class C1E(C1LoadGroup):
    """
    Instantaneous water heaters(12)
    """

    load_group = ["e"]
    load_group_description = "Instantaneous water heaters"
    notes = [c1_notes.C1Note12]

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # 33.3% connected load
        return sum(self.rating_a) * 0.33

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        # 6 A per living unit
        return 6 * self.num_living_units

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        # 6 A per living unit
        return 6 * self.num_living_units

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        # 100 A + 0.8 A per living unit
        return 100 + 0.8 * self.num_living_units


class C1F(C1LoadGroup):
    """
    Storage water heaters(13)
    """

    load_group = ["f"]
    load_group_description = "Storage water heaters"
    notes = [c1_notes.C1Note13]

    def _calculate_maximum_demand_a_1_living_unit(self) -> float:
        # Full-load current
        return sum(self.rating_a)

    def _calculate_maximum_demand_a_2_to_5_living_units(self) -> float:
        # 6 A per living unit
        return 6 * self.num_living_units

    def _calculate_maximum_demand_a_6_to_20_living_units(self) -> float:
        # 6 A per living unit
        return 6 * self.num_living_units

    def _calculate_maximum_demand_a_21_plus_living_units(self) -> float:
        # 100 A + 0.8 A per living unit
        return 100 + 0.8 * self.num_living_units


class C1G(C1LoadGroup):
    """
    Spa and swimming pool heaters
    """

    load_group = ["g"]
    load_group_description = "Spa and swimming pool heaters"
    notes = [c1_notes.C1Note14]

    def __init__(self, rating=None, num_load=1, rating_type="A", num_living_units=1):
        super().__init__(rating, num_load, rating_type, num_living_units)
        raise NotImplementedError(
            "This load group is currently not supported."
        )  # FIXME

        # 75% of the largest spa, plus 75% of the largest swimming pool,
        # plus 25% of the remainder


class C1H(C1LoadGroup):
    """
    Communal lighting
    """

    load_group = ["h"]
    load_group_description = "Communal lighting"
    notes = [c1_notes.C1Note6, c1_notes.C1Note7]

    def __init__(
        self,
        rating: float | list[float] | None = None,
        num_load: int = 1,
        rating_type: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        super().__init__(rating, num_load, rating_type, num_living_units)
        if self.num_loads == 1:
            raise LoadGroupNotApplicableException(self.__class__, self.num_loads)

    def _calculate_maximum_demand_a_2_to_5_living_units(self):
        # Full connected load
        return sum(self.rating_a)

    def _calculate_maximum_demand_a_6_to_20_living_units(self):
        # Full connected load
        return sum(self.rating_a)

    def _calculate_maximum_demand_a_21_plus_living_units(self):
        # Full connected load
        return sum(self.rating_a)


class C1I(C1LoadGroup):
    """
    Socket-outlets not included in load groups (j) and (m)
    below(8, 10, 14)
    Not applicable 2 A per point, up to a maximum of 15 A
    Permanently connected electrical equipment not
    exceeding 10 A
    """

    load_group = ["i"]
    load_group_description = (
        "Socket-outlets not included in load groups (j) and (m) "
        "below. Permanently connected electrical equipment not "
        "exceeding 10 A"
    )
    notes = [c1_notes.C1Note8, c1_notes.C1Note10, c1_notes.C1Note14]

    def __init__(
        self,
        rating: float | list[float] | None = None,
        num_load: int = 1,
        rating_type: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        super().__init__(rating, num_load, rating_type, num_living_units)
        if self.num_loads == 1:
            raise LoadGroupNotApplicableException(self.__class__, self.num_loads)

    def _calculate_maximum_demand_a_2_to_5_living_units(self):
        # 2 A per point, up to a maximum of 15 A
        return min(2 * self.num_loads, 15)

    def _calculate_maximum_demand_a_6_to_20_living_units(self):
        # 2 A per point, up to a maximum of 15 A
        return min(2 * self.num_loads, 15)

    def _calculate_maximum_demand_a_21_plus_living_units(self):
        # 2 A per point, up to a maximum of 15 A
        return min(2 * self.num_loads, 15)


class C1J1(C1LoadGroup):
    """
    Appliances rated at more than 10 A and socket-outlets
    for the connection thereof
    Clothes dryers, water heaters, self-heating washing
    machines, wash boilers(8)
    """

    load_group = ["j", 1]
    load_group_description = (
        "Appliances rated at more than 10 A and socket-outlets "
        "for the connection thereof — "
        "Clothes dryers, water heaters, "
        "self-heating washing machines, wash boilers"
    )
    notes = [c1_notes.C1Note8]

    def __init__(
        self,
        rating: float | list[float] | None = None,
        num_load: int = 1,
        rating_type: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        super().__init__(rating, num_load, rating_type, num_living_units)
        if self.num_loads == 1:
            raise LoadGroupNotApplicableException(self.__class__, self.num_loads)

    def _calculate_maximum_demand_a_2_to_5_living_units(self):
        # 50% connected load
        return sum(self.rating_a) * 0.5

    def _calculate_maximum_demand_a_6_to_20_living_units(self):
        # 50% connected load
        return sum(self.rating_a) * 0.5

    def _calculate_maximum_demand_a_21_plus_living_units(self):
        # 50% connected load
        return sum(self.rating_a) * 0.5


class C1J2(C1LoadGroup):
    load_group = ["j", 2]
    load_group_description = (
        "Appliances rated at more than 10 A and socket-outlets "
        "for the connection thereof — "
        "Fixed space heating, airconditioning equipment, "
        "saunas"
    )
    notes = [c1_notes.C1Note11]

    def __init__(
        self,
        rating: float | list[float] | None = None,
        num_load: int = 1,
        rating_type: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        super().__init__(rating, num_load, rating_type, num_living_units)
        if self.num_loads == 1:
            raise LoadGroupNotApplicableException(self.__class__, self.num_loads)

    def _calculate_maximum_demand_a_2_to_5_living_units(self):
        # 75% connected load
        return sum(self.rating_a) * 0.75

    def _calculate_maximum_demand_a_6_to_20_living_units(self):
        # 75% connected load
        return sum(self.rating_a) * 0.75

    def _calculate_maximum_demand_a_21_plus_living_units(self):
        # 75% connected load
        return sum(self.rating_a) * 0.75


class C1J3(C1LoadGroup):
    load_group = ["j", 3]
    load_group_description = (
        "Appliances rated at more than 10 A and socket-outlets "
        "for the connection thereof — "
        "Spa and swimming pool heaters"
    )

    def __init__(
        self,
        rating: float | list[float] | None = None,
        num_load: int = 1,
        rating_type: Literal["A", "W"] = "A",
        num_living_units: int = 1,
    ):
        super().__init__(rating, num_load, rating_type, num_living_units)
        if self.num_loads == 1:
            raise LoadGroupNotApplicableException(self.__class__, self.num_loads)
        else:
            raise NotImplementedError(
                "This load group is currently not supported."
            )  # FIXME
            # 75% of the largest spa plus 75% of the largest swimming pool,
            # plus 25% of the remainder


class C1J4(C1LoadGroup):
    load_group = ["j", 4]
    load_group_description = (
        "Appliances rated at more than 10 A and socket-outlets "
        "for the connection thereof — "
        "Charging equipment associated with electric vehicles"
    )

    def _calculate_maximum_demand_a_1_living_unit(self):
        # Fully connected load
        return sum(self.rating_a)

    def _calculate_maximum_demand_a_2_to_5_living_units(self):
        # 100% connected load
        return sum(self.rating_a)

    def _calculate_maximum_demand_a_6_to_20_living_units(self):
        # 90% connected load
        return sum(self.rating_a) * 0.9

    def _calculate_maximum_demand_a_21_plus_living_units(self):
        # 75% connected load
        return sum(self.rating_a) * 0.75


class C1K(C1LoadGroup):
    load_group = ["k"]
    load_group_description = "Lifts"


class C1L(C1LoadGroup):
    load_group = ["l"]
    load_group_description = "Motors"


class C1M(C1LoadGroup):
    load_group = ["m"]
    load_group_description = (
        "Appliances, including socket-outlets other than those set"
        "out in load groups (a) to (l) above, e.g. pottery kilns,"
        "welding machines, radio transmitters, X-ray equipment"
        "and the like"
    )
    load_group_exception = [
        C1A1,
        C1A2,
        C1B1,
        C1B2,
        C1B3,
        C1C,
        C1D,
        C1E,
        C1F,
        C1G,
        C1H,
        C1J1,
        C1J2,
        C1J3,
        C1J4,
        C1L,
    ]


# Resolve forward references
C1A1.load_group_exception = [C1A2, C1H]
C1B2.load_group_exception = [C1C, C1D, C1E, C1F, C1G, C1L]
C1B3.load_group_exception = [C1C, C1D, C1E, C1F, C1G, C1L]
