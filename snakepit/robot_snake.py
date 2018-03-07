from typing import List, Tuple

from snakepit.datatypes import Vector


class World:
    COLOR_0 = 0
    CH_VOID = ' '
    CH_STONE = '#'

    def __init__(self, size_x: int, size_y: int, data: List[List[Tuple[str, int]]]):
        self.SIZE_X = size_x
        self.SIZE_Y = size_y
        self.worlddata = data

    def __getitem__(self, item: int):
        return self.worlddata[item]


class BaseSnake:
    COLOR_0 = World.COLOR_0
    CH_VOID = World.CH_VOID
    CH_STONE = World.CH_STONE

    CH_HEAD = '@'
    CH_BODY = '*'
    CH_TAIL = '$'
    BODY_CHARS = frozenset([CH_HEAD, CH_BODY, CH_TAIL])

    CH_DEAD_HEAD = 'x'
    CH_DEAD_BODY = '+'
    CH_DEAD_TAIL = '%'
    DEAD_BODY_CHARS = frozenset([CH_DEAD_HEAD, CH_DEAD_BODY, CH_DEAD_TAIL])

    UP = Vector(0, -1)
    DOWN = Vector(0, 1)
    LEFT = Vector(-1, 0)
    RIGHT = Vector(1, 0)

    DIRECTIONS = (UP, DOWN, LEFT, RIGHT)

    color = None
    alive = False


class RobotSnake(BaseSnake):
    def __init__(self, world: World):
        self._world = world

    @property
    def world(self):
        """A two dimensional array of [y][x] that also has SIZE_X and SIZE_Y properties"""
        return self._world

    def next_direction(self, initial=False):
        raise NotImplementedError
