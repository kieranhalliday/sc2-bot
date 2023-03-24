import enum


class AddOnType(enum.Enum):
    REACTOR = 0
    TECHLAB = 1
    EMPTY = 2


class AddOnMovementType(enum.Enum):
    LIFT = 0
    LAND = 1
