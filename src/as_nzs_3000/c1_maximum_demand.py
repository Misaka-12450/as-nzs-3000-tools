from __future__ import annotations

import textwrap

_NOMINAL_VOLTAGE = 230


class IncorrectLoadGroupException(Exception):
    def __init__(self, correct_group: type[C1LoadGroup], reason: str = ""):
        self.correct_group = correct_group
        msg = f"Use {repr(correct_group)} ({correct_group.__name__}) instead."
        if reason:
            msg = f"{reason} {msg}"
        super().__init__(msg)


class _C1NoteMeta(type):
    def __str__(cls) -> str:
        return f"{cls.NUM}. {textwrap.dedent(cls.NOTE).strip()}"


class C1Note(metaclass=_C1NoteMeta):
    """
    Notes for Table C1 load groups.
    """

    NUM: int
    NOTE: str


class C1Note4(C1Note):
    NUM = 4
    NOTE: str = "Lighting track systems are regarded as two points per metre of track."


class C1Note6(C1Note):
    NUM = 6
    NOTE: str = """
    In the calculation of the connected load, the following ratings are assigned to lighting:
        
    (a) Incandescent lamps 60 W or the actual wattage of the lamp to be installed,
    whichever is the greater, except if the design of the luminaire associated with the
    lampholder only permits lamps of less than 60 W to be inserted in any
    lampholder, in which case, the connected load of that lampholder is the wattage
    of the highest rated lamp that may be accommodated. For multi-lamp luminaires,
    the load for each lampholder is assessed on the above basis.

    (b) Fluorescent and other discharge lamps Full connected load, i.e. the actual
    current consumed by the lighting arrangement, including the losses of auxiliary
    equipment, such as ballasts and capacitors.

    (c) Lighting tracks (230 V) 0.5 A/m per phase of track or the actual connected load,
    whichever is the greater.
    """


class C1Note7(C1Note):
    NUM = 7
    NOTE: str = (
        "Floodlighting, swimming pool lighting, tennis court lighting and the like."
    )


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
    :cvar rule_1_unit_per_phase: Calculation rules for single domestic installations.
    :cvar notes: Notes applicable to the load group.

    :ivar num: Number of units.
    :ivar rating_a: Rating per unit in amperes.
    :ivar rating_w: Rating per unit in watts.
    """

    load_group: list[str | int] = []
    load_group_description: str = ""
    load_group_exception: list[C1LoadGroup] = []
    rule_1_unit_per_phase: str = ""
    notes: list[C1Note] = []

    def __init__(
        self, num: int = 1, rating_a: float | None = None, rating_w: float | None = None
    ):
        if num > 0:
            self.num = num
        else:
            raise ValueError("num must be greater than zero.")

        if rating_a is not None and rating_a > 0:
            self.rating_a = rating_a
            self.rating_w = rating_a * _NOMINAL_VOLTAGE
        elif rating_w is not None and rating_w > 0:
            self.rating_w = rating_w
            self.rating_a = rating_w / _NOMINAL_VOLTAGE
        else:
            raise ValueError(
                "Either rating_a or rating_w that is greater than zero must be provided."
            )

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

        if self.rule_1_unit_per_phase:
            s = self._add_strings(s, self.rule_1_unit_per_phase)

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
    Lighting except (ii) and load group (h) below
    """

    load_group = ["a", 1]
    load_group_description = "Lighting except (ii) and load group (h) below"
    load_group_exception = []
    rule_1_unit_per_phase = (
        "3 A for 1 to 20 points + 2 A "
        "for each additional 20 points "
        "or part thereof"
    )
    notes = [C1Note4, C1Note6]

    def get_maximum_demand_a(self) -> float:
        if self.num <= 20:
            return 3
        return 3 + 2 * (self.num // 20)


class C1A2(C1LoadGroup):
    """
    Outdoor lighting exceeding a total of 1000 W
    """

    load_group = ["a", 2]
    load_group_description = "Outdoor lighting exceeding a total of 1000 W"
    load_group_exception = []
    rule_1_unit_per_phase = "75% connected load"
    notes = [C1Note6, C1Note7]

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
        return self.num * self.rating_a * 0.75


class C1H(C1LoadGroup):
    """
    Not applicable
    """

    load_group = ["h"]
    load_group_description = "Communal lighting"
    rule_1_unit_per_phase = "Not applicable"
    notes = [C1Note6, C1Note7]


# Resolve forward references
C1A1.load_group_exception = [C1A2, C1H]
