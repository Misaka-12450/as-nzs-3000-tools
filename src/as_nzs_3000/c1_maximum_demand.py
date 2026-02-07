from __future__ import annotations

from as_nzs_3000 import c1_notes

_NOMINAL_VOLTAGE = 230


class IncorrectLoadGroupException(Exception):
    def __init__(self, correct_group: type[C1LoadGroup], reason: str = ""):
        self.correct_group = correct_group
        msg = f"Use {repr(correct_group)} ({correct_group.__name__}) instead."
        if reason:
            msg = f"{reason} {msg}"
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
    """
    Class for calculating maximum demand for various load types.
    Based on AS/NZS 3000 Table C1.

    :cvar load_group: The load group name.
    :cvar load_group_description: Description of the load group.
    :cvar load_group_exception: Loads in other load groups and excluded from this load group.
    :cvar notes: Notes applicable to the load group.

    :ivar num: Number of units.
    :ivar rating_a: Rating per unit in amperes.
    :ivar rating_w: Rating per unit in watts.
    """

    load_group: list[str | int] = []
    load_group_description: str = ""
    load_group_exception: list[C1LoadGroup] = []
    notes: list[c1_notes.C1Note] = []

    def __init__(
        self,
        num: int = 1,
        rating_a: float | None = None,
        rating_w: float | None = None,
        num_living_units: int = 1,
    ):
        if num > 0:
            self.num = num
        else:
            raise ValueError("num must be greater than zero.")

        if (rating_a is not None and rating_a > 0) and (
            rating_w is not None and rating_w > 0
        ):
            if abs(rating_w - rating_a * _NOMINAL_VOLTAGE) > 1e-6:
                raise ValueError(
                    "rating_a and rating_w are inconsistent with each other."
                )
            self.rating_a = rating_a
            self.rating_w = rating_w
        elif rating_a is not None and rating_a > 0:
            self.rating_a = rating_a
            self.rating_w = rating_a * _NOMINAL_VOLTAGE
        elif rating_w is not None and rating_w > 0:
            self.rating_w = rating_w
            self.rating_a = rating_w / _NOMINAL_VOLTAGE
        else:
            raise ValueError(
                "Either rating_a or rating_w that is greater than zero must be provided."
            )

        if num_living_units > 0:
            self.num_living_units = num_living_units
        else:
            raise ValueError("num_living_units must be greater than zero.")

    @staticmethod
    def _add_strings(s1: str, s2: str, n: int = 2) -> str:
        """
        Add two strings together, and newline characters in-between if both strings are not empty.
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

    def get_maximum_demand_a(self) -> float:
        """
        Calculate the maximum demand in amperes.
        :return: The total amperes as calculated according to the rules.
        """
        return self.num * self.rating_a

    def get_maximum_demand_w(self) -> float:
        """
        Calculate the maximum demand in watts.
        :return: The total watts as calculated according to the rules.
        """
        return self.get_maximum_demand_a() * _NOMINAL_VOLTAGE


class C1A1(C1LoadGroup):
    """
    Lighting except (ii) and load group (h) below(4, 6)
    """

    load_group = ["a", 1]
    load_group_description = "Lighting except (ii) and load group (h) below"
    notes = [c1_notes.C1Note4, c1_notes.C1Note6]

    def get_maximum_demand_a(self) -> float:
        if self.num_living_units == 1:
            if self.num <= 20:
                return 3
            return 3 + 2 * (self.num // 20)


class C1A2(C1LoadGroup):
    """
    Outdoor lighting exceeding a total of 1000 W(6, 7)
    """

    load_group = ["a", 2]
    load_group_description = "Outdoor lighting exceeding a total of 1000 W"
    notes = [c1_notes.C1Note6, c1_notes.C1Note7]

    def __init__(
        self, num: int = 1, rating_a: float | None = None, rating_w: float | None = None
    ):
        super().__init__(num=num, rating_a=rating_a, rating_w=rating_w)
        if self.rating_w * self.num < 1000:
            raise IncorrectLoadGroupException(
                C1A1,
                f"Total wattage ({self.rating_w * self.num} W) does not exceed 1000 W.",
            )

    def get_maximum_demand_a(self) -> float:
        if self.num_living_units == 1:
            return self.num * self.rating_a * 0.75


class C1B1(C1LoadGroup):
    """
    Socket-outlets not exceeding 10 A(5, 8). Permanently
    connected electrical equipment not exceeding 10 A
    and not included in other load groups(9)
    """

    load_group = ["b", 1]
    load_group_description = (
        "Socket-outlets not exceeding 10 A. Permanently "
        "connected electrical equipment not exceeding 10 A "
        "and not included in other load groups"
    )
    notes = [c1_notes.C1Note5, c1_notes.C1Note8, c1_notes.C1Note9]

    def get_maximum_demand_a(self) -> float:
        if self.num_living_units == 1:
            if self.num <= 20:
                return 10
            return 10 + 5 * (self.num // 20)


class C1B2(C1LoadGroup):
    """
    Where the electrical installation includes one or
    more 15 A socket-outlets, other than socket-outlets
    provided to supply electrical equipment set out in
    load groups (c), (d), (e), (f), (g) and (l)(8, 10)
    """

    load_group = ["b", 2]
    load_group_description = (
        "Where the electrical installation includes one or "
        "more 15 A socket-outlets, other than socket-outlets "
        "provided to supply electrical equipment set out in "
        "load groups (c), (d), (e), (f), (g) and (l)"
    )
    notes = [c1_notes.C1Note8, c1_notes.C1Note10]

    def get_maximum_demand_a(self) -> float:
        if self.num_living_units == 1:
            return 10


class C1B3(C1LoadGroup):
    """
    Where the electrical installation includes one or
    more 20 A socket-outlets, other than socket-outlets
    provided to supply electrical equipment set out in
    load groups (c), (d), (e), (f), (g) and (l)(8, 10)
    """

    load_group = ["b", 3]
    load_group_description = (
        "Where the electrical installation includes one or "
        "more 20 A socket-outlets, other than socket-outlets "
        "provided to supply electrical equipment set out in "
        "load groups (c), (d), (e), (f), (g) and (l)"
    )
    notes = [c1_notes.C1Note8, c1_notes.C1Note10]

    def get_maximum_demand_a(self) -> float:
        if self.num_living_units == 1:
            return 15


class C1C(C1LoadGroup):
    """
    Ranges, cooking appliances, laundry equipment or
    socket-outlets rated at more than 10 A for the
    connection thereof(8)
    """

    load_group = ["c"]
    load_group_description = """
        Ranges, cooking appliances, laundry equipment or
        socket-outlets rated at more than 10 A for the
        connection thereof
        """
    notes = [c1_notes.C1Note8]

    def get_maximum_demand_a(self) -> float:
        if self.num_living_units == 1:
            return self.num * self.rating_a * 0.5


class C1D(C1LoadGroup):
    load_group = ["d"]


class C1E(C1LoadGroup):
    load_group = ["e"]


class C1F(C1LoadGroup):
    load_group = ["f"]


class C1G(C1LoadGroup):
    load_group = ["g"]


class C1H(C1LoadGroup):
    """
    Communal lighting
    """

    load_group = ["h"]
    load_group_description = "Communal lighting"
    notes = [c1_notes.C1Note6, c1_notes.C1Note7]


class C1I(C1LoadGroup):
    load_group = ["i"]


class C1J(C1LoadGroup):
    load_group = ["j"]


class C1K(C1LoadGroup):
    load_group = ["k"]


class C1L(C1LoadGroup):
    load_group = ["l"]


class C1M(C1LoadGroup):
    load_group = ["m"]


# Resolve forward references
C1A1.load_group_exception = [C1A2, C1H]
C1B2.load_group_exception = [C1C, C1D, C1E, C1F, C1G, C1L]
C1B3.load_group_exception = [C1C, C1D, C1E, C1F, C1G, C1L]
