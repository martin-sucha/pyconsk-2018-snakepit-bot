from collections import deque

import time

from asnake import Snake, IntTuple, GameState, MyRobotSnake, DIR_RIGHT
from snakepit.robot_snake import World
from test_asnake import parse_world

world, world_size = parse_world([
    '                                                                                ',
    '  $1*1@1                                                    83                  ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '    81                                                                          ',
    '    81                                                                          ',
    '                                                                                ',
    '                                                                                ',
])
snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
snake1.length = 3
snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])
snake1.grow_uncertain = True
snake1.grow = 1
snake1.score = 5
state = GameState(world, world_size, {1: snake1})
state.my_snake = snake1
robot = MyRobotSnake(World(world_size.x, world_size.y, world))
snake_directions = {1: DIR_RIGHT}

new_world, new_world_size = parse_world([
    '                                                                                ',
    '    $1*1@1                                                  83                  ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '                                                                                ',
    '    81                                                                          ',
    '    81                                                                          ',
    '                                                                                ',
    '                                                                                ',
])

new_world_wrapper = World(new_world_size.x, new_world_size.y, new_world)


def advance():
    return robot.advance_game(state, snake_directions)


def observe():
    return robot.observe_state_changes(state, new_world_wrapper, 1)


def search():
    return robot.search_move_space(3, state, robot.heuristic)


def bfs(time_limit=None):
    if time_limit is None:
        deadline = None
    else:
        deadline = time.monotonic() + time_limit
    return robot.bfs_food_and_partitions(state, deadline=deadline)


#print(timeit.timeit('robot.advance_game(state, snake_directions)', globals=globals(), number=1000))
