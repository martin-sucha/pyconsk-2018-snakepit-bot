import logging
import random
from collections import deque, defaultdict, namedtuple
from typing import List, Optional, Dict, Tuple, Union, Callable, Any

import time

from snakepit.robot_snake import RobotSnake


logger = logging.getLogger('mysnake')


XY = namedtuple('XY', 'x y')


DIR_UP = XY(0, -1)
DIR_RIGHT = XY(1, 0)
DIR_DOWN = XY(0, 1)
DIR_LEFT = XY(-1, 0)


class Snake:
    __slots__ = 'alive', 'head_pos', 'tail_pos', 'length', 'color', 'grow_uncertain', 'grow', 'score', 'head_history'

    def __init__(self, alive: bool, head_pos: XY, tail_pos: XY, color: int = 0):
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

    @property
    def direction(self) -> Optional[XY]:
        if len(self.head_history) == 0:
            return None
        prev_pos = self.head_history[0]
        return XY(self.head_pos.x - prev_pos.x, self.head_pos.y - prev_pos.y)

    def copy(self):
        copied = Snake(self.alive, self.head_pos, self.tail_pos, self.color)
        copied.length = self.length
        copied.grow_uncertain = self.grow_uncertain
        copied.grow = self.grow
        copied.score = self.score
        copied.head_history = self.head_history.copy()
        return copied

    def __repr__(self):
        return '<{!r} snake of length {!r} at {!r} grow {}{!r}>'.format(self.color, self.length, self.head_pos,
                                                                        '~' if self.grow_uncertain else '', self.grow)


def neighbours(position):
    """Return 4 neighbouring positions around a given position"""
    yield XY(position.x, position.y - 1)  # up
    yield XY(position.x + 1, position.y)  # right
    yield XY(position.x, position.y + 1)  # bottom
    yield XY(position.x - 1, position.y)  # left


WORLD_VOID = 0
# 1..9 are yummies
WORLD_TAIL = 10
WORLD_BODY = 11
WORLD_HEAD = 12
WORLD_DEAD_TAIL = 13
WORLD_DEAD_BODY = 14
WORLD_DEAD_HEAD = 15
WORLD_STONE = 16

GAME_CHARS = {
    ' ': WORLD_VOID,
    '1': 1,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,
    RobotSnake.CH_TAIL: WORLD_TAIL,
    RobotSnake.CH_BODY: WORLD_BODY,
    RobotSnake.CH_HEAD: WORLD_HEAD,
    RobotSnake.CH_DEAD_TAIL: WORLD_DEAD_TAIL,
    RobotSnake.CH_DEAD_BODY: WORLD_DEAD_BODY,
    RobotSnake.CH_DEAD_HEAD: WORLD_DEAD_HEAD,
    RobotSnake.CH_STONE: WORLD_STONE,
}


class GameState:
    __slots__ = 'world_size', 'world', 'snakes_by_color', 'my_snake', 'enemy_snake', 'frame_no'

    def __init__(self, world: Union[List[List[Tuple[str, int]]], 'GameState'], world_size: Optional[XY] = None,
                 snakes_by_color: Optional[Dict[int, Snake]] = None, frame_no: Optional[int] = None):
        if isinstance(world, GameState):
            self.world_size = world.world_size
            self.world = bytearray(world.world)
            self.snakes_by_color = {k: v.copy() for k, v in world.snakes_by_color.items()}
            self.my_snake = None  # type: Optional[Snake]
            self.enemy_snake = None  # type: Optional[Snake]
            if world.my_snake is not None:
                self.my_snake = self.snakes_by_color[world.my_snake.color]
            if world.enemy_snake is not None:
                self.enemy_snake = self.snakes_by_color[world.enemy_snake.color]
            self.frame_no = world.frame_no
        else:
            self.world_size = world_size
            self.world = bytearray(world_size.x * world_size.y)
            index = 0
            for y in range(self.world_size.y):
                for x in range(self.world_size.x):
                    char, color = world[y][x]
                    self.world[index] = GAME_CHARS[char] | (color << 5)
                    index += 1
            self.snakes_by_color = snakes_by_color
            self.my_snake = None  # type: Optional[Snake]
            self.enemy_snake = None  # type: Optional[Snake]
            self.frame_no = frame_no

    @staticmethod
    def _encode_value(value: Tuple[int, int]) -> int:
        """Encode a given tuple of char, color to a single byte"""
        char, color = value
        return char | (color << 5)

    @staticmethod
    def _decode_value(byte: int) -> Tuple[int, int]:
        return byte & 0x1f, byte >> 5

    def world_iter(self):
        index = 0
        for y in range(self.world_size.y):
            for x in range(self.world_size.x):
                yield x, y, self._decode_value(self.world[index])
                index += 1

    def world_get(self, position: XY) -> Tuple[int, int]:
        """Get the state of world at given position.

        This does bounds checks and returns stones for positions outside of the play area to simplify the code.

        :return tuple of (world char, color)
        """
        if position.x < 0 or position.x >= self.world_size.x:
            return WORLD_STONE, 0
        if position.y < 0 or position.y >= self.world_size.y:
            return WORLD_STONE, 0
        return self._decode_value(self.world[position.y * self.world_size.x + position.x])

    def world_get2(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Get the state of world at given position.

        This does bounds checks and returns stones for positions outside of the play area to simplify the code.

        :return tuple of (world char, color)
        """
        position_x, position_y = position
        if position_x < 0 or position_x >= self.world_size.x:
            return WORLD_STONE, 0
        if position_y < 0 or position_y >= self.world_size.y:
            return WORLD_STONE, 0
        return self._decode_value(self.world[position_y * self.world_size.x + position_x])

    def world_set(self, position: XY, value: Tuple[int, int]):
        """Set the state of world at given position.

        This does bounds checks.
        """
        if position.x < 0 or position.x >= self.world_size.x:
            return
        if position.y < 0 or position.y >= self.world_size.y:
            return
        self.world[position.y * self.world_size.x + position.x] = self._encode_value(value)

    def trace_snake_path(self, start_pos: XY) -> List[XY]:
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
                if WORLD_TAIL <= candidate_char <= WORLD_HEAD and candidate_color == color:
                    paths.append(candidate_position)

            if len(paths) != 1:
                # either no other position to move to - we have found the end of the snake already
                # or too many positions to move to - we can't determine the history of movement of the snake
                # in either case, we need to stop
                break

            segments.append(paths[0])

        return segments

    def mark_dead(self, dead_color: int):
        trans = bytes.maketrans(bytes([
            WORLD_HEAD | (dead_color << 5),
            WORLD_BODY | (dead_color << 5),
            WORLD_TAIL | (dead_color << 5),
        ]), bytes([
            WORLD_DEAD_HEAD,
            WORLD_DEAD_BODY,
            WORLD_DEAD_TAIL,
        ]))
        self.world = self.world.translate(trans)
        self.snakes_by_color[dead_color].alive = False


class SearchTimedOut(Exception):
    pass


BFSPosition = namedtuple('BFSPosititon', ('position', 'partition_size', 'food_score'))
BFSResult = namedtuple('BFSResult', ('position_stats', 'fully_explored_distance'))


class MyRobotSnake(RobotSnake):
    def __init__(self, *args, **kwargs):
        super(MyRobotSnake, self).__init__(*args, **kwargs)
        self.old_state = None  # type: Optional[GameState]
        self.frame_no = 0

    @staticmethod
    def observe_state_changes(old_state: Optional[GameState], world, my_color: int) -> GameState:
        """Observe what has changed since last turn and produce new game state"""
        if old_state:
            snakes_by_color = old_state.snakes_by_color
            frame_no = old_state.frame_no + 1
        else:
            snakes_by_color = {}
            frame_no = 0
        new_state = GameState(world, XY(world.SIZE_X, world.SIZE_Y), snakes_by_color, frame_no)

        # decrease grow by one
        for snake in new_state.snakes_by_color.values():
            snake.grow = max(0, snake.grow - 1)

        tails_by_color = {}
        old_tails_by_color = {}
        heads_by_color = {}
        lengths_by_color = defaultdict(lambda: 0)
        index = 0
        for y in range(new_state.world_size.y):
            for x in range(new_state.world_size.x):
                encoded = new_state.world[index]
                char = encoded & 0x1f
                color = encoded >> 5

                if char == WORLD_TAIL:
                    tails_by_color[color] = XY(x, y)
                elif char == WORLD_HEAD:
                    heads_by_color[color] = XY(x, y)

                if WORLD_TAIL <= char <= WORLD_HEAD:
                    lengths_by_color[color] += 1

                index += 1
        if old_state:
            index = 0
            for y in range(old_state.world_size.y):
                for x in range(old_state.world_size.x):
                    encoded = old_state.world[index]
                    char = encoded & 0x1f
                    color = encoded >> 5

                    if char == WORLD_TAIL:
                        old_tails_by_color[color] = XY(x, y)

                    index += 1

        for color, position in heads_by_color.items():
            needs_trace = False
            if color in new_state.snakes_by_color:
                snake = new_state.snakes_by_color[color]

                if position in neighbours(snake.head_pos):
                    snake.head_history.appendleft(snake.head_pos)
                    snake.length += 1
                    if old_state:
                        old_char, old_color = old_state.world_get(position)
                        if 1 <= old_char <= 9:
                            snake.grow += old_char
                            snake.score += old_char
                else:
                    needs_trace = True

                snake.head_pos = position
                snake.tail_pos = tails_by_color[color]
            else:
                snake = new_state.snakes_by_color[color] = Snake(True, position, tails_by_color[color], color)
                needs_trace = True

            old_tail_pos = old_tails_by_color.get(color)
            if old_tail_pos is not None and old_tail_pos != snake.tail_pos:
                if len(snake.head_history) > 0 and snake.head_history[-1] == old_tail_pos:
                    snake.head_history.pop()

                if snake.grow_uncertain:
                    # the tail has moved, so grow was definitely 0 last turn
                    snake.grow_uncertain = False

            snake.length = lengths_by_color[color]
            if needs_trace:
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
        if new_state.enemy_snake is None:
            enemy_snakes = list(snake for snake in new_state.snakes_by_color.values() if snake.color != my_color)
            if enemy_snakes:
                new_state.enemy_snake = enemy_snakes[0]

        return new_state

    @staticmethod
    def advance_game(state: GameState, snake_directions: Dict[int, XY]) -> Tuple[GameState, bool]:
        """Advance the state of game one tick, based on the selected snake directions.

        :param state: starting game state
        :param snake_directions: a dictionary from snake color to direction of movement
        :return: a new game state based on the directions
        """
        next_snake_heads = {color: XY(state.snakes_by_color[color].head_pos.x + direction.x,
                                      state.snakes_by_color[color].head_pos.y + direction.y)
                            for color, direction in snake_directions.items()}
        tails = {snake.tail_pos: color
                 for color, snake in state.snakes_by_color.items()}
        new_state = GameState(state)  # copy state
        new_state.frame_no += 1
        uncertainty = False  # True if we are not certain things will go this way

        kills = defaultdict(list)  # dict from killer to killed color
        dies = set()
        moves = set()

        def should_grow(snake):
            nonlocal uncertainty
            if len(snake.head_history) != snake.length - 1:
                # we don't know where tail will move, leave it where it is
                uncertainty = True
                logger.info('uncertain because snake {} does not have full history {}/{}'.format(
                    snake.color, len(snake.head_history), snake.length))
                return True
            if snake.grow_uncertain:
                uncertainty = True
                logger.info('uncertain because snake {} has grow_uncertain=True'.format(snake.color))
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
                if WORLD_DEAD_TAIL <= old_char <= WORLD_STONE:
                    # snake dies, does not move, does not get points
                    dies.add(color)
                    continue
                if WORLD_BODY <= old_char <= WORLD_HEAD:
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
                if 1 <= old_char <= 9:
                    new_snake = new_state.snakes_by_color[color]
                    new_snake.grow += old_char
                    new_snake.score += old_char
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
                new_state.world_set(new_tail, (WORLD_TAIL, new_snake.color))
                new_snake.tail_pos = new_tail
            new_snake.head_history.appendleft(new_snake.head_pos)
            new_state.world_set(new_snake.head_pos, (WORLD_BODY, new_snake.color))
            new_snake.head_pos = next_snake_heads[color]
            new_state.world_set(new_snake.head_pos, (WORLD_HEAD, new_snake.color))
            avoids_void.add(new_snake.head_pos)

        # Cleanup any tails that were not overwritten
        for void_pos in needs_void - avoids_void:
            new_state.world_set(void_pos, (WORLD_VOID, 0))

        # Repaint dead snakes and mark them as not alive
        for color in dies:
            new_state.mark_dead(color)

        # Resolve points for killing
        for color in dies:
            kills.pop(color, None)
        for killer_color, victims in kills.items():
            new_state.snakes_by_color[killer_color].score += len(victims) * 1000

        return new_state, uncertainty

    @staticmethod
    def bfs_food_and_partitions(state: GameState, deadline: Optional[float]):
        """Explore world and for each head direction, find out food score and graph partition size.

        The food score is sum of food/distance for the positions that are closest from the head direction.
        Partition size is number of reachable nodes in the partition from that size.

        :param state: The game state
        :param deadline: Optional deadline (as time.monotonic() value)
        """
        visited_positions = set()
        positions_to_visit = deque()  # contains tuples (position, distance, food_value, initial_index)
        enqueued_positions = {}

        # Initially, we need to visit any of the reachable neighbours of our snake head
        head_pos = state.my_snake.head_pos
        initial_positions = []
        for neighbour in ((head_pos.x, head_pos.y - 1), (head_pos.x + 1, head_pos.y),
                          (head_pos.x, head_pos.y + 1), (head_pos.x - 1, head_pos.y)):
            char, color = state.world_get2(neighbour)
            if char < WORLD_TAIL:  # not occupied
                # char is also food value in this case
                positions_to_visit.append((neighbour, 1, char, len(initial_positions)))
                enqueued_positions[neighbour] = len(initial_positions)
                initial_positions.append(neighbour)

        food_score = [0.0] * len(initial_positions)  # sum of food/distance for initial position
        reachable_node_count = [0] * len(initial_positions)
        partition_index = list(range(len(initial_positions)))  # for union-find-set
        fully_explored_distance = 0  # how far we have explored within the time limit

        def find(index):
            cur_index = index
            while partition_index[cur_index] != cur_index:
                cur_index = partition_index[cur_index]
            partition_index[index] = cur_index
            return cur_index

        def union(index1, index2):
            root1 = find(index1)
            root2 = find(index2)
            if root1 != root2:
                partition_index[root2] = root1

        while positions_to_visit and (deadline is None or time.monotonic() < deadline):
            position, distance, food_value, initial_index = positions_to_visit.popleft()

            if position in visited_positions:
                continue

            fully_explored_distance = distance - 1
            reachable_node_count[initial_index] += 1
            food_score[initial_index] += food_value/distance

            position_x, position_y = position

            for neighbour in ((position_x, position_y - 1), (position_x + 1, position_y),
                              (position_x, position_y + 1), (position_x - 1, position_y)):
                if neighbour in enqueued_positions:
                    union(initial_index, enqueued_positions[neighbour])
                    continue
                char, color = state.world_get2(neighbour)
                if char < WORLD_TAIL:  # not occupied
                    # char is also food value in this case
                    positions_to_visit.append((neighbour, distance + 1, char, initial_index))
                    enqueued_positions[neighbour] = initial_index

            visited_positions.add(position)

        merged_reachable_node_count = [0] * len(initial_positions)

        for initial_index in range(len(initial_positions)):
            merged_reachable_node_count[find(initial_index)] += reachable_node_count[initial_index]

        position_stats = []
        for index, position in enumerate(initial_positions):
            partition = find(index)
            position_stats.append(BFSPosition(position, merged_reachable_node_count[partition], food_score[index]))

        return BFSResult(position_stats, fully_explored_distance)

    @staticmethod
    def heuristic(state: GameState, bfs: BFSResult, bfs_branch: Optional[BFSPosition], depth: int):
        """Larger return values are better for my_snake"""
        if bfs_branch is None:
            bfs_branch = BFSPosition((0, 0), 0, 0.0)

        me_lives = state.my_snake is not None and state.my_snake.alive
        my_length = state.my_snake.length if state.my_snake is not None else 0
        enemy_lives = state.enemy_snake is not None and state.enemy_snake.alive
        my_score = 0 if state.my_snake is None else state.my_snake.score
        enemy_score = 0 if state.enemy_snake is None else state.enemy_snake.score

        # The game is limited to 8192 frames
        if state.frame_no > 8192:
            me_lives = False
            enemy_lives = False

        game_result = 0

        if me_lives and enemy_lives:
            liveness = 0
        elif me_lives:
            liveness = 1
            if my_score > enemy_score:  # I win
                game_result = 1
        elif enemy_lives:
            liveness = -1
            if my_score < enemy_score:  # I lose
                game_result = -1
        else:
            liveness = 0
            # game over
            if my_score > enemy_score:
                game_result = 1  # I win
            elif my_score < enemy_score:
                game_result = -1  # I lose
            else:
                game_result = 0  # draw

        score = my_score - enemy_score

        if bfs.fully_explored_distance >= depth:
            entering_small_partition = -1 if bfs_branch.partition_size < my_length else 0
        else:
            entering_small_partition = 0

        return (game_result, liveness, entering_small_partition, score, bfs_branch.food_score,
                bfs_branch.partition_size, depth if game_result < 0 or liveness < 0 else -depth)

    def iterative_search_move_space(self,
                                    game_state: GameState,
                                    heuristic: Callable[[GameState, Optional[BFSPosition]], Any],
                                    deadline: Optional[float],
                                    bfs: BFSResult) -> Tuple[Any, Optional[XY], int]:
        best_move = None
        best_score = None
        total_explored_states = 0
        depth = 1
        while True:
            try:
                score, move, explored_states = self.search_move_space(0, depth, game_state, heuristic, deadline, None,
                                                                      bfs)
            except SearchTimedOut:
                logger.info('Search timed out in depth {}'.format(depth))
                return best_score, best_move, total_explored_states
            else:
                total_explored_states += explored_states
                best_move = move
                best_score = score
                depth += 1

    def search_move_space(self,
                          depth: int,
                          max_depth: int,
                          game_state: GameState,
                          heuristic: Callable[[GameState, Optional[BFSPosition]], Any],
                          deadline: Optional[float],
                          bfs_branch: Optional[BFSPosition],
                          bfs: BFSResult) -> Tuple[Any, Optional[XY], int]:
        moves = [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT]
        if depth == max_depth or not game_state.my_snake.alive:
            return heuristic(game_state, bfs, bfs_branch, depth), None, 0

        best_move = None
        best_score = None
        explored_states = 0
        for my_move in moves:
            my_direction = game_state.my_snake.direction
            if my_direction is not None and my_move.x == -my_direction.x and my_move.y == -my_direction.y:
                continue  # can't move backwards

            if bfs_branch is not None:
                move_bfs_branch = bfs_branch
            else:
                next_head_pos = XY(game_state.my_snake.head_pos.x + my_move.x,
                                   game_state.my_snake.head_pos.y + my_move.y)
                logger.info('Next head: {}'.format(next_head_pos))
                for branch in bfs.position_stats:
                    logger.info('Branch: {}'.format(branch))
                    if branch.position == (next_head_pos.x, next_head_pos.y):
                        move_bfs_branch = branch
                        break
                else:
                    move_bfs_branch = BFSPosition((next_head_pos.x, next_head_pos.y), 0, 0.0)

            if game_state.enemy_snake and game_state.enemy_snake.alive:
                enemy_direction = game_state.enemy_snake.direction
                worst_enemy_move = None
                worst_enemy_score = None
                for enemy_move in moves:
                    if enemy_direction is not None and enemy_move.x == -enemy_direction.x and \
                            enemy_move.y == -enemy_direction.y:
                        continue  # can't move backwards
                    if deadline is not None and time.monotonic() > deadline:
                        raise SearchTimedOut()
                    snake_directions = {
                        game_state.my_snake.color: my_move,
                        game_state.enemy_snake.color: enemy_move,
                    }
                    explored_states += 1
                    new_state, uncertainty = self.advance_game(game_state, snake_directions)
                    if uncertainty:
                        logger.info('uncertain')
                        score = heuristic(new_state, bfs, move_bfs_branch, depth)
                    else:
                        score, _, explored_substates = self.search_move_space(depth + 1, max_depth, new_state,
                                                                              heuristic, deadline,
                                                                              move_bfs_branch, bfs)
                        explored_states += explored_substates

                    if worst_enemy_move is None or score < worst_enemy_score:
                        worst_enemy_move = enemy_move
                        worst_enemy_score = score

                logger.info('{} {} {}'.format(depth, worst_enemy_move, worst_enemy_score))
                if best_move is None or worst_enemy_score > best_score:
                    best_move = my_move
                    best_score = worst_enemy_score
            else:
                if deadline is not None and time.monotonic() > deadline:
                    raise SearchTimedOut()
                snake_directions = {
                    game_state.my_snake.color: my_move,
                }
                explored_states += 1
                new_state, uncertainty = self.advance_game(game_state, snake_directions)
                if uncertainty:
                    logger.info('uncertain')
                    score = heuristic(new_state, bfs, move_bfs_branch, depth)
                else:
                    score, _, explored_substates = self.search_move_space(depth + 1, max_depth, new_state,
                                                                          heuristic, deadline,
                                                                          move_bfs_branch, bfs)
                    explored_states += explored_substates
                if best_move is None or score > best_score:
                    best_move = my_move
                    best_score = score

        return best_score, best_move, explored_states

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
        tick_start_time = time.monotonic()
        self.frame_no += 1
        logger.info('------------- tick start {}'.format(self.frame_no))
        # the frame rate is 9 at the beginning and goes up to 60 later
        # so we can run deeper searches in the first 1024 frames (we use 1000 to have some buffer)
        # the deadline is 3/4 the frame time, to allow for replies, etc.

        if self.frame_no < 0:
            tick_time_timit = 0.75 * (1 / 9.0)
        else:
            tick_time_limit = 0.75 * (1 / 60.0)
        tick_deadline = tick_start_time + tick_time_limit
        logger.info('time limit: {}ms'.format(tick_time_limit*1000))

        if self.old_state:
            for snake in self.old_state.snakes_by_color.values():
                logger.info('old {!r} {!r} {} {}'.format(snake, snake.score, 'alive' if snake.alive else 'dead',
                                                     snake.head_history))
        start_time = time.monotonic()
        game_state = self.observe_state_changes(self.old_state, self.world, self.color)
        end_time = time.monotonic()
        logger.info('Observe took {} milliseconds'.format((end_time - start_time) * 1000))
        for snake in game_state.snakes_by_color.values():
            logger.info('{!r} {!r} {} {}'.format(snake, snake.score, 'alive' if snake.alive else 'dead',
                                                 snake.head_history))

        logger.info('Selecting next move')

        logger.info('Running BFS')
        start_time = time.monotonic()
        bfs = self.bfs_food_and_partitions(game_state, start_time + tick_time_limit / 4)
        end_time = time.monotonic()
        logger.info('BFS took {} ms, explored to distance {}'.format((end_time - start_time) * 1000,
                                                                     bfs.fully_explored_distance))

        start_time = time.monotonic()
        best_score, best_move, explored_states = self.iterative_search_move_space(game_state,
                                                                                  self.heuristic,
                                                                                  tick_deadline,
                                                                                  bfs)
        end_time = time.monotonic()
        logger.info('Iterative search took {} ms, explored {} states'.format((end_time - start_time) * 1000,
                                                                             explored_states))

        if best_move is None:
            # Something bad has happened as we could not search depth 1. At least try to use some simple fallback.
            logger.error('No possible moves found. Using fallback strategy.')
            if len(bfs.position_stats) > 0:
                my_length = game_state.my_snake.length if game_state.my_snake is not None else 0

                options = []
                for bfs_pos in bfs.position_stats:
                    entering_small_partition = -1 if bfs_pos.partition_size < my_length else 0
                    heur = (entering_small_partition, bfs_pos.food_score, bfs_pos.partition_size)
                    options.append((heur, bfs_pos.position))
                best = max(options, key=lambda x: x[0])
                best_move = XY(best[1][0], best[1][1])
            else:
                # try to follow a tail, we have no other option
                for direction in DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT:
                    dir_char, dir_color = game_state.world_get(XY(game_state.my_snake.head_pos.x + direction.x,
                                                                  game_state.my_snake.head_pos.y + direction.y))
                    if dir_char == WORLD_TAIL:
                        best_move = direction
                        break

            non_dying_moves = []
            my_direction = game_state.my_snake.direction
            for direction in DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT:
                if my_direction is not None and direction.x == -my_direction.x and direction.y == -my_direction.y:
                    continue  # can't move backwards
                dir_char, dir_color = game_state.world_get(XY(game_state.my_snake.head_pos.x + direction.x,
                                                              game_state.my_snake.head_pos.y + direction.y))
                if dir_char < WORLD_TAIL:  # not occupied
                    # dir_char is also food value in this case
                    non_dying_moves.append((dir_char, direction))
                elif dir_char == WORLD_TAIL:
                    non_dying_moves.append((-1, direction))
            if non_dying_moves:
                random.shuffle(non_dying_moves)  # sort is stable, so will preserve the shuffle on the same level
                non_dying_moves.sort(key=lambda i: i[0])
                best_move = non_dying_moves[-1][1]

        logger.info('My position: ' + repr(game_state.my_snake.head_pos))
        logger.info('Next move {!r} score {!r}'.format(best_move, best_score))

        # copy the old version of the world for reference
        self.old_state = game_state

        logger.info('Next direction returning after {} ms'.format((time.monotonic() - tick_start_time)*1000))
        # convert relative move to one of the documented return values
        # we could have converted to snakepit.datatypes.Vector directly, but it is not documented that it will be
        # accessible, so it's better to be safe than sorry
        if best_move == DIR_UP:
            return self.UP
        elif best_move == DIR_RIGHT:
            return self.RIGHT
        elif best_move == DIR_DOWN:
            return self.DOWN
        elif best_move == DIR_LEFT:
            return self.LEFT
        else:
            logger.error('Invalid value of best_move, falling back to the same direction')
            return None
