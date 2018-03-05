import logging
import random
from collections import deque
from typing import List, Optional, Dict, Tuple

from snakepit.robot_snake import RobotSnake


logger = logging.getLogger('mysnake')


class IntTuple:
    """Helper for nicer position/vector arithmetics"""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if not isinstance(other, IntTuple):
            return NotImplemented
        return IntTuple(self.x + other.x, self.y + other.y)

    def __iadd__(self, other):
        if not isinstance(other, IntTuple):
            return NotImplemented
        self.x += other.x
        self.y += other.y

        return self

    def __sub__(self, other):
        if not isinstance(other, IntTuple):
            return NotImplemented
        return IntTuple(self.x - other.x, self.y - other.y)

    def __isub__(self, other):
        if not isinstance(other, IntTuple):
            return NotImplemented
        self.x -= other.x
        self.y -= other.y

        return self

    def __eq__(self, other):
        if not isinstance(other, IntTuple):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        if not isinstance(other, IntTuple):
            return NotImplemented
        return self.x != other.x or self.y != other.y

    def __repr__(self):
        return '<{!r}, {!r}>'.format(self.x, self.y)


class AliveSnake:
    def __init__(self, head_pos: IntTuple, tail_pos: IntTuple, color: int = 0):
        self.head_pos = head_pos
        self.tail_pos = tail_pos
        self.length = None  # type: Optional[int]
        self.color = color
        self.grow = None  # type: Optional[int]
        # history of head positions, up to and including tail. may end earlier than tail though, if we joined later in
        # the game and we have not observed the previous movements of the snake. does not contain the current head
        # position.
        self.head_history = deque()

    def __repr__(self):
        return '<{!r} snake of length {!r} at >'.format(self.color, self.length, self.head_pos)


def neighbours(position):
    """Return 4 neighbouring positions around a given position"""
    yield position + IntTuple(0, -1)  # up
    yield position + IntTuple(1, 0)  # right
    yield position + IntTuple(0, 1)  # bottom
    yield position + IntTuple(-1, 0)  # left


class MyRobotSnake(RobotSnake):
    OCCUPIED_CHARS = RobotSnake.DEAD_BODY_CHARS\
        .union(RobotSnake.BODY_CHARS).union([RobotSnake.CH_STONE])\
        .difference(RobotSnake.CH_TAIL)

    def __init__(self, *args, **kwargs):
        super(MyRobotSnake, self).__init__(*args, **kwargs)
        self.snakes_by_color = {}  # type: Dict[int, AliveSnake]
        self.my_snake = None  # type: Optional[AliveSnake]

    def world_get(self, position) -> Tuple[str, Optional[int]]:
        """Get a state of world at given position.

        This does bounds checks and returns stones for positions outside of the play area to simplify the code.

        :return tuple of (world char, color)
        """
        if position.x < 0 or position.x >= self.world.SIZE_X:
            return self.CH_STONE, None
        if position.y < 0 or position.y >= self.world.SIZE_Y:
            return self.CH_STONE, None
        return self.world[position.y][position.x]

    def trace_snake_path(self, start_pos: IntTuple) -> List[IntTuple]:
        """Given a head or tail position of the snake, find the segments of the path until they can be uniquely followed.

        We might find cycles in case the snake touches itself. In this case, we can't determine the history of the
        snake movement just from world state in a given instant.

        :return a list of snake segments, starting at start_pos
        """

        char, color = self.world_get(start_pos)

        segments = [start_pos]
        while True:
            current_pos = segments[-1]
            paths = []
            for candidate_position in neighbours(current_pos):
                if len(segments) > 1 and candidate_position == segments[-2]:
                    continue
                candidate_char, candidate_color = self.world_get(candidate_position)
                if candidate_char in self.BODY_CHARS and candidate_color == color:
                    paths.append(candidate_position)

            if len(paths) != 1:
                # either no other position to move to - we have found the end of the snake already
                # or too many positions to move to - we can't determine the history of movement of the snake
                # in either case, we need to stop
                break

            segments.append(paths[0])

        return segments

    def world_positions(self):
        for y in range(self.world.SIZE_Y):
            for x in range(self.world.SIZE_X):
                yield IntTuple(x, y)

    def extract_snakes(self):
        """Update positions of all snakes in the world"""
        tails_by_color = {}
        for position in self.world_positions():
            char, color = self.world_get(position)
            if char == self.CH_TAIL:
                tails_by_color[color] = position

        for position in self.world_positions():
            char, color = self.world_get(position)
            if char in self.CH_HEAD:
                needs_trace = False
                if color in self.snakes_by_color:
                    snake = self.snakes_by_color[color]

                    if position in neighbours(snake.head_pos):
                        snake.head_history.appendleft(snake.head_pos)
                    else:
                        needs_trace = True
                    snake.head_pos = position
                else:
                    snake = self.snakes_by_color[color] = AliveSnake(position, tails_by_color[color], color)
                    needs_trace = True

                if needs_trace:
                    path = self.trace_snake_path(snake.head_pos)
                    snake.head_history = deque(path[1:])

        if self.my_snake is None:
            self.my_snake = self.snakes_by_color[self.color]

    def next_direction(self, initial=False):
        """
        This method sends the next direction of the robot snake to the server.
        The direction is changed on the next frame load.

        The return value should be one of: `self.UP`, `self.DOWN`, `self.LEFT`, `self.RIGHT` or `None`.

        The snake's world (`self.world`) is a two-dimensional array that changes during each frame.
        Each point in the matrix is a two-item tuple `(char, color)`.

        Each snake has a different color represented by an integer.
        Your snake's color is available in `self.color`.

        More information can be found in the Snake documentation.
        """
        logger.info('Updating snakes')
        self.extract_snakes()

        logger.info('Selecting next move')
        candidates = []  # next_head_positions where I won't definitely die
        for neighbour in neighbours(self.my_snake.head_pos):
            candidate_char, candidate_color = self.world_get(neighbour)
            if candidate_char not in self.OCCUPIED_CHARS:
                candidates.append(neighbour)

        if not candidates:
            # we don't have any option where to move and die after the turn
            return None

        next_move = random.choice(candidates)
        relative_move = (next_move - self.my_snake.head_pos)
        logger.info('My position: ' + repr(self.my_snake.head_pos))
        logger.info('Candidates: ' + repr(candidates))
        logger.info('Next move: ' + repr(relative_move))

        # convert relative move to one of the documented return values
        # we could have converted to snakepit.datatypes.Vector directly, but it is not documented that it will be
        # accessible, so it's better to be safe than sorry
        if relative_move == IntTuple(0, -1):
            return self.UP
        elif relative_move == IntTuple(1, 0):
            return self.RIGHT
        elif relative_move == IntTuple(0, 1):
            return self.DOWN
        elif relative_move == IntTuple(-1, 0):
            return self.LEFT
        else:
            logger.error('Invalid value of relative_move, going in the same direction')
            return None
