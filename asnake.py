import logging
import random
from collections import deque, defaultdict
from fractions import Fraction
from typing import List, Optional, Dict, Tuple

import copy

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

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __repr__(self):
        return '<{!r}, {!r}>'.format(self.x, self.y)


DIR_UP = IntTuple(0, -1)
DIR_RIGHT = IntTuple(1, 0)
DIR_DOWN = IntTuple(0, 1)
DIR_LEFT = IntTuple(-1, 0)


class Snake:
    def __init__(self, alive: bool, head_pos: IntTuple, tail_pos: IntTuple, color: int = 0):
        self.alive = alive
        self.head_pos = head_pos
        self.tail_pos = tail_pos
        self.length = None  # type: Optional[int]
        self.color = color
        self.grow_uncertain = True  # if true, the snake might still grow as we have incomplete observations
        self.grow = 0  # if this is >0, the snake will definitely grow for at least the specfied amount of ticks
        self.score = 0

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


class GameState:
    def __init__(self, world: List[List[Tuple[str, int]]], world_size: IntTuple,
                 snakes_by_color: Dict[int, Snake]):
        self.world = [list(row) for row in world]
        self.world_size = world_size
        self.snakes_by_color = snakes_by_color
        self.my_snake = None  # type: Optional[Snake]

    def world_positions(self):
        for y in range(self.world_size.y):
            for x in range(self.world_size.x):
                yield IntTuple(x, y)

    def world_get(self, position: IntTuple) -> Tuple[str, int]:
        """Get the state of world at given position.

        This does bounds checks and returns stones for positions outside of the play area to simplify the code.

        :return tuple of (world char, color)
        """
        if position.x < 0 or position.x >= self.world_size.x:
            return RobotSnake.CH_STONE, 0
        if position.y < 0 or position.y >= self.world_size.y:
            return RobotSnake.CH_STONE, 0
        return self.world[position.y][position.x]

    def world_set(self, position: IntTuple, value: Tuple[str, int]):
        """Set the state of world at given position.

        This does bounds checks.
        """
        if position.x < 0 or position.x >= self.world_size.x:
            return
        if position.y < 0 or position.y >= self.world_size.y:
            return
        self.world[position.y][position.x] = value

    def world_yummy(self, position: IntTuple) -> int:
        """Return yummy value at the given position. If the position is not edible, return 0"""
        char, color = self.world_get(position)
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
                if candidate_char in RobotSnake.BODY_CHARS and candidate_color == color:
                    paths.append(candidate_position)

            if len(paths) != 1:
                # either no other position to move to - we have found the end of the snake already
                # or too many positions to move to - we can't determine the history of movement of the snake
                # in either case, we need to stop
                break

            segments.append(paths[0])

        return segments

    def mark_dead(self, dead_color: int):
        replacement = {
            RobotSnake.CH_HEAD: RobotSnake.CH_DEAD_HEAD,
            RobotSnake.CH_BODY: RobotSnake.CH_DEAD_BODY,
            RobotSnake.CH_TAIL: RobotSnake.CH_DEAD_TAIL,
        }
        for position in self.world_positions():
            char, color = self.world_get(position)
            if char in RobotSnake.BODY_CHARS and color == dead_color:
                self.world_set(position, (replacement[char], 0))
        self.snakes_by_color[dead_color].alive = False


class MyRobotSnake(RobotSnake):
    OCCUPIED_CHARS = RobotSnake.DEAD_BODY_CHARS\
        .union(RobotSnake.BODY_CHARS).union([RobotSnake.CH_STONE])\
        .difference(RobotSnake.CH_TAIL)

    def __init__(self, *args, **kwargs):
        super(MyRobotSnake, self).__init__(*args, **kwargs)
        self.old_state = None  # type: Optional[GameState]

    @staticmethod
    def observe_state_changes(old_state: GameState, world, my_color: int) -> GameState:
        """Observe what has changed since last turn and produce new game state"""
        if old_state:
            snakes_by_color = old_state.snakes_by_color
        else:
            snakes_by_color = {}
        new_state = GameState(world, IntTuple(world.SIZE_X, world.SIZE_Y), snakes_by_color)

        # decrease grow by one
        for snake in new_state.snakes_by_color.values():
            snake.grow = max(0, snake.grow - 1)

        tails_by_color = {}
        old_tails_by_color = {}
        lengths_by_color = defaultdict(lambda: 0)
        for position in new_state.world_positions():
            char, color = new_state.world_get(position)
            if char == RobotSnake.CH_TAIL:
                tails_by_color[color] = position
            if char in RobotSnake.BODY_CHARS:
                lengths_by_color[color] += 1

        if old_state:
            for position in old_state.world_positions():
                old_char, old_color = old_state.world_get(position)
                if old_char == RobotSnake.CH_TAIL:
                    old_tails_by_color[old_color] = position

        for position in new_state.world_positions():
            char, color = new_state.world_get(position)
            if char in RobotSnake.CH_HEAD:
                needs_trace = False
                if color in new_state.snakes_by_color:
                    snake = new_state.snakes_by_color[color]

                    if position in neighbours(snake.head_pos):
                        snake.head_history.appendleft(snake.head_pos)
                        if old_state:
                            old_yummy = old_state.world_yummy(position)
                            if old_yummy > 0:
                                logger.info('Snake {} has eaten {} last turn'.format(snake.color, old_yummy))
                                snake.grow += old_yummy
                                snake.score += old_yummy
                    else:
                        needs_trace = True

                    snake.head_pos = position
                else:
                    snake = new_state.snakes_by_color[color] = Snake(True, position, tails_by_color[color], color)
                    needs_trace = True

                old_tail_pos = old_tails_by_color.get(color)
                if snake.grow_uncertain and old_tail_pos is not None and old_tail_pos != snake.tail_pos:
                    # the tail has moved, so grow was definitely 0 last turn
                    logger.info('Snake {} has stopped growing last turn'.format(snake.color))
                    snake.grow_uncertain = False

                snake.length = lengths_by_color[color]
                if needs_trace:
                    logger.info('Tracing snake {}'.format(snake.color))
                    path = new_state.trace_snake_path(snake.head_pos)
                    snake.head_history = deque(path[1:])
                    snake.grow = 0
                    snake.grow_uncertain = True

        alive_snake_colors = set(tails_by_color.keys())
        for color, snake in new_state.snakes_by_color.items():
            if color not in alive_snake_colors:
                snake.alive = False

        if new_state.my_snake is None:
            new_state.my_snake = new_state.snakes_by_color[my_color]

        return new_state

    @staticmethod
    def advance_game(state: GameState, snake_directions: Dict[int, IntTuple]) -> Tuple[GameState, bool]:
        """Advance the state of game one tick, based on the selected snake directions.

        :param state: starting game state
        :param snake_directions: a dictionary from snake color to direction of movement
        :return: a new game state based on the directions
        """
        next_snake_heads = {color: state.snakes_by_color[color].head_pos + direction
                            for color, direction in snake_directions.items()}
        tails = {snake.tail_pos: color
                 for color, snake in state.snakes_by_color.items()}
        new_state = copy.deepcopy(state)
        uncertainty = False  # True if we are not certain things will go this way

        kills = defaultdict(list)  # dict from killer to killed color
        dies = set()
        moves = set()

        def should_grow(snake):
            nonlocal uncertainty
            if len(snake.head_history) != snake.length - 1:
                # we don't know where tail will move, leave it where it is
                uncertainty = True
                return True
            if snake.grow_uncertain:
                uncertainty = True
                return True
            return snake.grow

        dependencies = {}  # dict from color to color
        for color, pos in next_snake_heads.items():
            if pos in tails:
                dependencies[color] = tails[pos]

        # Snakes can crash heads frontally: $*@ @*$ -> %+x+%, find those cases
        # note these still might depend on another snake
        next_snake_heads_inv = defaultdict(list)
        for color, pos in next_snake_heads.items():
            next_snake_heads_inv[pos].append(color)

        # topological sort dependencies
        # this is special cased for two-snake game, TODO add support for multiple players later
        colors = list(next_snake_heads.keys())
        if len(colors) == 2 and dependencies.get(colors[0]) == colors[1] and dependencies.get(colors[1]) == colors[0]:
            # tail cycle, we need to break it explicitly
            snake0 = state.snakes_by_color[colors[0]]
            snake1 = state.snakes_by_color[colors[1]]
            if should_grow(snake0) or should_grow(snake1):
                # snake0 and snake1 both die and don't move, neither gets points
                dies.add(colors[0])
                dies.add(colors[1])
            else:
                moves.add(colors[0])
                moves.add(colors[1])
        else:
            tsorted = sorted(colors, key=lambda color: 1 if color in dependencies else 0)

            for color in tsorted:
                if color in dependencies:
                    # tail chase
                    other_snake = state.snakes_by_color[dependencies[color]]
                    if color == dependencies[color]:
                        # self-chase, pretend we can move
                        moves.add(color)
                    if should_grow(other_snake) or not dependencies[color] in moves:
                        # snake dies, does not move
                        if color == dependencies[color]:
                            moves.remove(color)  # we pretended to move
                        else:
                            # other_snake gets credit for killing us
                            kills[other_snake.color].append(color)
                        dies.add(color)
                        continue
                    # fallthrough
                old_char, old_color = state.world_get(next_snake_heads[color])
                if old_char in RobotSnake.DEAD_BODY_CHARS or old_char == RobotSnake.CH_STONE:
                    # snake dies, does not move, does not get points
                    dies.add(color)
                    continue
                if old_char in (RobotSnake.CH_HEAD, RobotSnake.CH_BODY):
                    # snake dies, does not move, old_color possibly gets points (if does not die in this turn)
                    dies.add(color)
                    kills[old_color].append(color)
                    continue
                if len(next_snake_heads_inv[next_snake_heads[color]]) > 1:
                    # frontal collision. snake dies, moves, does not get points
                    dies.add(color)
                    moves.add(color)
                    continue
                # did not crash into anything, so lives, moves
                if old_char.isdigit():
                    new_snake = new_state.snakes_by_color[color]
                    new_snake.grow += int(old_char)
                    new_snake.score += int(old_char)
                moves.add(color)

        # Move snakes
        needs_void = set()
        avoids_void = set()
        for color in moves:
            snake = state.snakes_by_color[color]
            new_snake = new_state.snakes_by_color[color]
            if should_grow(snake):
                new_snake.length += 1
                new_snake.grow -= 1
            else:
                old_tail = new_snake.head_history.pop()
                new_tail = new_snake.head_history[-1]
                needs_void.add(old_tail)
                new_state.world_set(new_tail, (RobotSnake.CH_TAIL, new_snake.color))
                new_snake.tail_pos = new_tail
            new_snake.head_history.appendleft(new_snake.head_pos)
            new_state.world_set(new_snake.head_pos, (RobotSnake.CH_BODY, new_snake.color))
            new_snake.head_pos = next_snake_heads[color]
            new_state.world_set(new_snake.head_pos, (RobotSnake.CH_HEAD, new_snake.color))
            avoids_void.add(new_snake.head_pos)

        # Cleanup any tails that were not overwritten
        for void_pos in needs_void - avoids_void:
            new_state.world_set(void_pos, (RobotSnake.CH_VOID, 0))

        # Repaint dead snakes and mark them as not alive
        for color in dies:
            new_state.mark_dead(color)

        # Resolve points for killing
        for color in dies:
            kills.pop(color, None)
        for killer_color, victims in kills.items():
            new_state.snakes_by_color[killer_color].score += len(victims) * 1000

        return new_state, uncertainty

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
        game_state = self.observe_state_changes(self.old_state, self.world, self.color)
        for snake in game_state.snakes_by_color.values():
            logger.info('{!r} {!r} {}'.format(snake, snake.score, 'alive' if snake.alive else 'dead'))

        logger.info('Selecting next move')

        def next_turn_occupied(position):
            """Return a fraction how likely a position will be occupied next turn"""
            char, color = game_state.world_get(position)
            rv_sum = Fraction(0)
            if char in self.OCCUPIED_CHARS:
                rv_sum += 1
            elif char == RobotSnake.CH_TAIL:
                if game_state.snakes_by_color[color].grow_uncertain:
                    rv_sum += Fraction(1, 2)  # we don't know whether it will grow or not
                elif game_state.snakes_by_color[color].grow > 0:
                    # the snake at this tail will definitely grow
                    rv_sum += 1
                elif color != self.color:
                    # the snake may still eat something in the next turn, which will leave the tail in place
                    for neighbour in neighbours(game_state.snakes_by_color[color].head_pos):
                        if game_state.world_yummy(neighbour):
                            rv_sum += Fraction(1, 3)
            for snake in game_state.snakes_by_color.values():
                if snake.color == self.color:
                    continue
                possibilities = []
                for neighbour in neighbours(snake.head_pos):
                    neighbour_char, neighbour_color = game_state.world_get(neighbour)
                    if neighbour_char not in self.OCCUPIED_CHARS:
                        possibilities.append(neighbour)
                for possibility in possibilities:
                    if possibility == position:
                        rv_sum += Fraction(1, len(possibilities))
            return rv_sum

        candidates = []  # next_head_positions where I won't definitely die
        for neighbour in neighbours(game_state.my_snake.head_pos):
            score = next_turn_occupied(neighbour)
            candidates.append((score, neighbour))

        if not candidates:
            # we don't have any option where to move and die after the turn
            return None

        min_score = min(x[0] for x in candidates)
        logger.info("Min score: " + repr(min_score))
        candidates2 = [candidate for score, candidate in candidates if score == min_score]

        next_move = random.choice(candidates2)

        relative_move = (next_move - game_state.my_snake.head_pos)
        logger.info('My position: ' + repr(game_state.my_snake.head_pos))
        logger.info('Candidates: ' + repr(candidates))
        logger.info('Next move: ' + repr(relative_move))

        # copy the old version of the world for reference
        self.old_state = game_state

        # convert relative move to one of the documented return values
        # we could have converted to snakepit.datatypes.Vector directly, but it is not documented that it will be
        # accessible, so it's better to be safe than sorry
        if relative_move == DIR_UP:
            return self.UP
        elif relative_move == DIR_RIGHT:
            return self.RIGHT
        elif relative_move == DIR_DOWN:
            return self.DOWN
        elif relative_move == DIR_LEFT:
            return self.LEFT
        else:
            logger.error('Invalid value of relative_move, going in the same direction')
            return None
