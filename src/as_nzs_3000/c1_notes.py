from __future__ import annotations

import textwrap


class _C1NoteMeta(type):
    def __str__(cls) -> str:
        return f"{cls.NUM}. {textwrap.dedent(cls.NOTE).strip()}"


class C1Note(metaclass=_C1NoteMeta):
    """
    Notes for Table C1 load groups.
    """

    NUM: int
    NOTE: str


class C1Note1(C1Note):
    NUM = 1


class C1Note2(C1Note):
    NUM = 2


class C1Note3(C1Note):
    NUM = 3


class C1Note4(C1Note):
    NUM = 4
    NOTE: str = "Lighting track systems are regarded as two points per metre of track."


class C1Note5(C1Note):
    NUM = 5
    NOTE = """
        A socket-outlet installed more than 2.3 m above a floor for the connection of a
        luminaire may be included as a lighting point in load group (a)(i).
        An appliance rated at not more than 150 W, which is permanently connected, or
        connected by means of a socket-outlet installed more than 2.3 m above a floor, may
        be included as a lighting point in load group (a)(i).
        """


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


class C1Note8(C1Note):
    NUM = 8
    NOTE: str = """
        For the purpose of determining maximum demand, a multiple combination socketoutlet
        is regarded as the same number of points as the number of integral socketoutlets
        in the combination.
        """


class C1Note9(C1Note):
    NUM = 9
    NOTE = """
        Each item of permanently connected electrical equipment not exceeding 10 A may be
        included in load group (b)(i) as an additional point.
        """


class C1Note10(C1Note):
    NUM = 10
