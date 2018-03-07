from collections import deque

from asnake import Snake, IntTuple, GameState, MyRobotSnake, DIR_RIGHT
from snakepit.robot_snake import World
from test_asnake import parse_world

world, world_size = parse_world([
    '                                                                                ',
    '  $1*1@1                                                                        ',
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
    '                                                                                ',
    '                                                                                ',
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
robot = MyRobotSnake(World(world_size.x, world_size.y, world))
snake_directions = {1: DIR_RIGHT}


def advance():
    return robot.advance_game(state, snake_directions)

#print(timeit.timeit('robot.advance_game(state, snake_directions)', globals=globals(), number=1000))
