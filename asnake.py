import logging
import random
from collections import deque, defaultdict
from fractions import Fraction
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
        self.grow_uncertain = True  # if true, the snake might still grow as we have incomplete observations
        self.grow = 0  # if this is >0, the snake will definitely grow for at least the specfied amount of ticks

        # history of head positions, up to and including tail. may end earlier than tail though, if we joined later in
        # the game and we have not observed the previous movements of the snake. does not contain the current head
        # position.
        self.head_history = deque()

    def __repr__(self):
        return '<{!r} snake of length {!r} at {!r} grow {}{!r}>'.format(self.color, self.length, self.head_pos,
                                                                        '~' if self.grow_uncertain else '', self.grow)


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
        self.old_world = None

    def world_get(self, position: IntTuple) -> Tuple[str, int]:
        """Get the state of world at given position.

        This does bounds checks and returns stones for positions outside of the play area to simplify the code.

        :return tuple of (world char, color)
        """
        if position.x < 0 or position.x >= self.world.SIZE_X:
            return self.CH_STONE, 0
        if position.y < 0 or position.y >= self.world.SIZE_Y:
            return self.CH_STONE, 0
        return self.world[position.y][position.x]

    def world_yummy(self, position: IntTuple) -> int:
        """Return yummy value at the given position. If the position is not edible, return 0"""
        char, color = self.world_get(position)
        if char.isdigit():
            return int(char)
        return 0

    def world_positions(self):
        for y in range(self.world.SIZE_Y):
            for x in range(self.world.SIZE_X):
                yield IntTuple(x, y)

    def old_world_get(self, position: IntTuple) -> Optional[Tuple[str, int]]:
        """Get the state of world in a previous turn.

        :return tuple of (world char, color)
        """
        if position.x < 0 or position.x >= self.world.SIZE_X:
            return self.CH_STONE, 0
        if position.y < 0 or position.y >= self.world.SIZE_Y:
            return self.CH_STONE, 0
        if self.old_world is None:
            return None
        return self.old_world[position.y][position.x]

    def old_world_yummy(self, position: IntTuple) -> Optional[int]:
        """Return yummy value at the given position in the previous turn. If the position is not edible return 0"""
        old_value = self.old_world_get(position)
        if old_value is None:
            return None
        char, color = old_value
        if char.isdigit():
            return int(char)
        return 0

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

    def extract_snakes(self):
        """Update positions of all snakes in the world"""
        # decrease grow by one
        for snake in self.snakes_by_color.values():
            snake.grow = max(0, snake.grow - 1)

        tails_by_color = {}
        old_tails_by_color = {}
        lengths_by_color = defaultdict(lambda: 0)
        for position in self.world_positions():
            char, color = self.world_get(position)
            if char == self.CH_TAIL:
                tails_by_color[color] = position
            if char in self.BODY_CHARS:
                lengths_by_color[color] += 1

        if self.old_world:
            for position in self.world_positions():
                old_char, old_color = self.old_world_get(position)
                if old_char == self.CH_TAIL:
                    old_tails_by_color[old_color] = position

        for position in self.world_positions():
            char, color = self.world_get(position)
            if char in self.CH_HEAD:
                needs_trace = False
                if color in self.snakes_by_color:
                    snake = self.snakes_by_color[color]

                    if position in neighbours(snake.head_pos):
                        snake.head_history.appendleft(snake.head_pos)
                        old_yummy = self.old_world_yummy(position)
                        if old_yummy is not None and old_yummy > 0:
                            logger.info('Snake {} has eaten {} last turn'.format(snake.color, old_yummy))
                            snake.grow += old_yummy - 1  # -1 because that one was already done by the game
                    else:
                        needs_trace = True

                    snake.head_pos = position
                else:
                    snake = self.snakes_by_color[color] = AliveSnake(position, tails_by_color[color], color)
                    needs_trace = True

                old_tail_pos = old_tails_by_color.get(color)
                if snake.grow_uncertain and old_tail_pos is not None and old_tail_pos != snake.tail_pos:
                    # the tail has moved, so grow was definitely 0 last turn
                    logger.info('Snake {} has stopped growing last turn'.format(snake.color))
                    snake.grow_uncertain = False

                snake.length = lengths_by_color[color]
                if needs_trace:
                    logger.info('Tracing snake {}'.format(snake.color))
                    path = self.trace_snake_path(snake.head_pos)
                    snake.head_history = deque(path[1:])
                    snake.grow = 0
                    snake.grow_uncertain = True

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
        for snake in self.snakes_by_color.values():
            logger.info(repr(snake))

        logger.info('Selecting next move')

        def next_turn_occupied(position):
            """Return a fraction how likely a position will be occupied next turn"""
            char, color = self.world_get(position)
            rv_sum = Fraction(0)
            if char in self.OCCUPIED_CHARS:
                rv_sum += 1
            elif char == self.CH_TAIL:
                if self.snakes_by_color[color].grow_uncertain:
                    rv_sum += Fraction(1, 2)  # we don't know whether it will grow or not
                elif self.snakes_by_color[color].grow > 0:
                    # the snake at this tail will definitely grow
                    rv_sum += 1
                elif color != self.color:
                    # the snake may still eat something in the next turn, which will leave the tail in place
                    for neighbour in neighbours(self.snakes_by_color[color].head_pos):
                        if self.world_yummy(neighbour):
                            rv_sum += Fraction(1, 3)
            for snake in self.snakes_by_color.values():
                if snake.color == self.color:
                    continue
                possibilities = []
                for neighbour in neighbours(snake.head_pos):
                    neighbour_char, neighbour_color = self.world_get(neighbour)
                    if neighbour_char not in self.OCCUPIED_CHARS:
                        possibilities.append(neighbour)
                for possibility in possibilities:
                    if possibility == position:
                        rv_sum += Fraction(1, len(possibilities))
            return rv_sum

        candidates = []  # next_head_positions where I won't definitely die
        for neighbour in neighbours(self.my_snake.head_pos):
            score = next_turn_occupied(neighbour)
            candidates.append((score, neighbour))

        if not candidates:
            # we don't have any option where to move and die after the turn
            return None

        min_score = min(x[0] for x in candidates)
        logger.info("Min score: " + repr(min_score))
        candidates2 = [candidate for score, candidate in candidates if score == min_score]

        next_move = random.choice(candidates2)

        relative_move = (next_move - self.my_snake.head_pos)
        logger.info('My position: ' + repr(self.my_snake.head_pos))
        logger.info('Candidates: ' + repr(candidates))
        logger.info('Next move: ' + repr(relative_move))

        # copy the old version of the world for reference
        self.old_world = [list(row) for row in self.world]

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
