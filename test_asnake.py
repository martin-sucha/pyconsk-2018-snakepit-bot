from collections import deque
from typing import Tuple, List

from asnake import GameState, IntTuple, Snake, MyRobotSnake, DIR_DOWN, DIR_RIGHT, DIR_UP
from snakepit.robot_snake import World


def parse_world(lines: List[str]) -> Tuple[List[List[Tuple[str, int]]], IntTuple]:
    """Parse the world lines to world data and world size"""
    size_y = len(lines)
    if len(lines[0]) % 2 != 0:
        raise ValueError('Odd character count in line')
    size_x = len(lines[0])//2
    rows = []
    for line in lines:
        if len(line) % 2 != 0:
            raise ValueError('Odd character count in line')
        if len(line) != size_x * 2:
            raise ValueError('Lines of different length')
        row = []
        for x in range(size_x):
            char = line[2*x]
            color_char = line[2*x + 1]
            if color_char.isdigit():
                color = int(color_char)
            else:
                color = 0
            row.append((char, color))
        rows.append(row)
    return rows, IntTuple(size_x, size_y)


def serialize_world(state: GameState) -> List[str]:
    """Serialize world data to lines"""
    def describe(x, y):
        char, color = state.world_get(IntTuple(x, y))
        return '{}{}'.format(char, ' ' if color < 1 or color > 9 else str(color))
    return [''.join(describe(x, y) for x in range(state.world_size.x)) for y in range(state.world_size.y)]


def test_parse_world():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '        ',
        '        ',
    ])
    assert world_size.x == 4
    assert world_size.y == 4
    assert len(world) == 4
    assert world == [
        [(' ', 0), (' ', 0), (' ', 0), (' ', 0)],
        [(' ', 0), ('$', 1), ('*', 1), ('@', 1)],
        [(' ', 0), (' ', 0), (' ', 0), (' ', 0)],
        [(' ', 0), (' ', 0), (' ', 0), (' ', 0)],
    ]


def test_serialize_world():
    lines = serialize_world(GameState([
        [(' ', 0), (' ', 0), (' ', 0), (' ', 0)],
        [(' ', 0), ('$', 1), ('*', 1), ('@', 1)],
        [(' ', 0), (' ', 0), (' ', 0), (' ', 0)],
        [(' ', 0), (' ', 0), (' ', 0), (' ', 0)],
    ], IntTuple(4, 4), {}))
    assert lines == [
        '        ',
        '  $1*1@1',
        '        ',
        '        ',
    ]


def test_advance_game_simple_move():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '        ',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])
    game_state = GameState(world, world_size, {1: snake1})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '    $1*1',
        '      @1',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(3, 1), IntTuple(2, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert not new_snake1.grow_uncertain


def test_advance_game_simple_grow():
    world, world_size = parse_world([
        '        ',
        '  $1*1*@',
        '        ',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 2
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])
    game_state = GameState(world, world_size, {1: snake1})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  $1*1*1',
        '      @1',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(3, 1), IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 4
    assert new_snake1.grow == 1
    assert not new_snake1.grow_uncertain


def test_advance_game_simple_eat():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '      21',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])
    game_state = GameState(world, world_size, {1: snake1})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '    $1*1',
        '      @1',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(3, 1), IntTuple(2, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 2
    assert new_snake1.score == 4 + 2
    assert not new_snake1.grow_uncertain


def test_advance_game_simple_eat_growing():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '      21',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 2
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])
    game_state = GameState(world, world_size, {1: snake1})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  $1*1*1',
        '      @1',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(3, 1), IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 4
    assert new_snake1.grow == 3
    assert new_snake1.score == 4 + 2
    assert not new_snake1.grow_uncertain


def test_advance_game_simple_crash_wall():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '        ',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])
    game_state = GameState(world, world_size, {1: snake1})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_RIGHT})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  % + x ',
        '        ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain


def test_advance_game_simple_crash_dead_tail():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '      % ',
        '    x + ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])
    game_state = GameState(world, world_size, {1: snake1})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  % + x ',
        '      % ',
        '    x + ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain


def test_advance_game_simple_crash_dead_body():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '    % + ',
        '    x + ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])
    game_state = GameState(world, world_size, {1: snake1})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  % + x ',
        '    % + ',
        '    x + ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain


def test_advance_game_simple_crash_dead_head():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '  % + x ',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])
    game_state = GameState(world, world_size, {1: snake1})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  % + x ',
        '  % + x ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain


def test_advance_game_simple_suicide():
    world, world_size = parse_world([
        '        ',
        '  $1*1*1',
        '    @1*1',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(2, 2), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 5
    snake1.score = 4
    snake1.head_history = deque([IntTuple(3, 2), IntTuple(3, 1), IntTuple(2, 1), IntTuple(1, 1)])
    game_state = GameState(world, world_size, {1: snake1})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_UP})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  % + + ',
        '    x + ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(3, 2), IntTuple(3, 1), IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 5
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain


def test_advance_game_simple_tail_grow_suicide():
    world, world_size = parse_world([
        '        ',
        '  $1*1*1',
        '  @1*1*1',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(1, 2), IntTuple(1, 1), 1)
    snake1.grow = 1
    snake1.grow_uncertain = False
    snake1.length = 6
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 2), IntTuple(3, 2), IntTuple(3, 1), IntTuple(2, 1), IntTuple(1, 1)])
    game_state = GameState(world, world_size, {1: snake1})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_UP})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  % + + ',
        '  x + + ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 2), IntTuple(3, 2), IntTuple(3, 1), IntTuple(2, 1),
                                             IntTuple(1, 1)]
    assert new_snake1.length == 6
    assert new_snake1.grow == 1
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain


def test_advance_game_simple_tail_chase():
    world, world_size = parse_world([
        '        ',
        '  $1*1*1',
        '  @1*1*1',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(1, 2), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 6
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 2), IntTuple(3, 2), IntTuple(3, 1), IntTuple(2, 1), IntTuple(1, 1)])
    game_state = GameState(world, world_size, {1: snake1})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_UP})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  @1$1*1',
        '  *1*1*1',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(1, 2), IntTuple(2, 2), IntTuple(3, 2), IntTuple(3, 1),
                                             IntTuple(2, 1)]
    assert new_snake1.length == 6
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain


def test_advance_game_double_move():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '  $2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_UP, 2: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '      @1',
        '    $1*1',
        '    $2*2',
        '      @2',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(3, 1), IntTuple(2, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(3, 2), IntTuple(2, 2)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_grow_one():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '  $2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 2
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_UP, 2: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '      @1',
        '  $1*1*1',
        '    $2*2',
        '      @2',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(3, 1), IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 4
    assert new_snake1.grow == 1
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(3, 2), IntTuple(2, 2)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_grow_two():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '  $2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 2), 2)
    snake2.grow = 1
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_UP, 2: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '      @1',
        '    $1*1',
        '  $2*2*2',
        '      @2',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(3, 1), IntTuple(2, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(3, 2), IntTuple(2, 2), IntTuple(1, 2)]
    assert new_snake2.length == 4
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_grow_both():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '  $2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 2
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 2), 2)
    snake2.grow = 1
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_UP, 2: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '      @1',
        '  $1*1*1',
        '  $2*2*2',
        '      @2',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(3, 1), IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 4
    assert new_snake1.grow == 1
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(3, 2), IntTuple(2, 2), IntTuple(1, 2)]
    assert new_snake2.length == 4
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_crash_to_dying_body():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '$2*2@2  ',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])

    snake2 = Snake(True, IntTuple(2, 2), IntTuple(0, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(1, 2), IntTuple(0, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_RIGHT, 2: DIR_UP})
    assert not uncertainty

    assert serialize_world(new_state) == [
        '        ',
        '  % + x ',
        '% + x   ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(1, 2), IntTuple(0, 2)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_crash_to_dying_body2():
    world, world_size = parse_world([
        '        ',
        '$1*1@1  ',
        '  $2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(2, 1), IntTuple(0, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(1, 1), IntTuple(0, 1)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_RIGHT})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '% + x   ',
        '  % + x ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(1, 1), IntTuple(0, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(2, 2), IntTuple(1, 2)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_crash_to_dying_tail():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '*2@2    ',
        '$2      ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])

    snake2 = Snake(True, IntTuple(1, 2), IntTuple(0, 3), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(0, 2), IntTuple(0, 3)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_RIGHT, 2: DIR_UP})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  % + x ',
        '+ x     ',
        '%       ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(0, 2), IntTuple(0, 3)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_crash_to_dying_tail2():
    world, world_size = parse_world([
        '$1      ',
        '*1@1    ',
        '  $2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(1, 1), IntTuple(0, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(0, 1), IntTuple(0, 0)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_RIGHT})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '%       ',
        '+ x     ',
        '  % + x ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(0, 1), IntTuple(0, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(2, 2), IntTuple(1, 2)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_crash_to_dying_head():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '  $2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_RIGHT, 2: DIR_UP})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  % + x ',
        '  % + x ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(2, 2), IntTuple(1, 2)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_crash_to_dying_head2():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '  $2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_RIGHT})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  % + x ',
        '  % + x ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(2, 2), IntTuple(1, 2)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_frontal_crash():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '  $2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_UP})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  % + x ',
        '  % + x ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(2, 2), IntTuple(1, 2)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_frontal_crash2():
    world, world_size = parse_world([
        '        ',
        '  $2*2@2',
        '  $1*1@1',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 2), IntTuple(1, 2), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 2), IntTuple(1, 2)])

    snake2 = Snake(True, IntTuple(3, 1), IntTuple(1, 1), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 1), IntTuple(1, 1)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_UP, 2: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '        ',
        '  % + x ',
        '  % + x ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 2), IntTuple(1, 2)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_frontal_crash3():
    world, world_size = parse_world([
        '  $1*1@1',
        '        ',
        '  $2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 0), IntTuple(1, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 0), IntTuple(1, 0)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_UP})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '    % + ',
        '      x ',
        '    % + ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(3, 0), IntTuple(2, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(3, 2), IntTuple(2, 2)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_frontal_crash3_eat():
    world, world_size = parse_world([
        '  $1*1@1',
        '      23',
        '  $2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(3, 0), IntTuple(1, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 0), IntTuple(1, 0)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_UP})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '    % + ',
        '      x ',
        '    % + ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(3, 0), IntTuple(2, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(3, 2), IntTuple(2, 2)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_tail_grow_kill():
    world, world_size = parse_world([
        '  @1*1$1',
        '  $2    ',
        '  *2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(1, 0), IntTuple(3, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 0), IntTuple(3, 0)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 1), 2)
    snake2.grow = 1
    snake2.grow_uncertain = False
    snake2.length = 4
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2), IntTuple(1, 1)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '  x + % ',
        '  $2    ',
        '  *2*2*2',
        '      @2',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 0), IntTuple(3, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(3, 2), IntTuple(2, 2), IntTuple(1, 2), IntTuple(1, 1)]
    assert new_snake2.length == 5
    assert new_snake2.grow == 0
    assert new_snake2.score == 1006
    assert not new_snake2.grow_uncertain


def test_advance_game_double_tail_chase():
    world, world_size = parse_world([
        '  @1*1$1',
        '  $2    ',
        '  *2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(1, 0), IntTuple(3, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 0), IntTuple(3, 0)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 1), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 4
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2), IntTuple(1, 1)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '  *1$1  ',
        '  @1    ',
        '  $2*2*2',
        '      @2',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(1, 0), IntTuple(2, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(3, 2), IntTuple(2, 2), IntTuple(1, 2)]
    assert new_snake2.length == 4
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_tail_chase_loop():
    world, world_size = parse_world([
        '  @1*1*1',
        '  $2  $1',
        '  *2*2@2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(1, 0), IntTuple(3, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 4
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 0), IntTuple(3, 0), IntTuple(3, 1)])

    snake2 = Snake(True, IntTuple(3, 2), IntTuple(1, 1), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 4
    snake2.score = 6
    snake2.head_history = deque([IntTuple(2, 2), IntTuple(1, 2), IntTuple(1, 1)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_UP})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '  *1*1$1',
        '  @1  @2',
        '  $2*2*2',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(1, 0), IntTuple(2, 0), IntTuple(3, 0)]
    assert new_snake1.length == 4
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(3, 2), IntTuple(2, 2), IntTuple(1, 2)]
    assert new_snake2.length == 4
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_tail_chase_frontal_crash():
    world, world_size = parse_world([
        '  @1*1*1',
        '@2$1  *1',
        '*2*1*1*1',
        '$2      ',
    ])
    snake1 = Snake(True, IntTuple(1, 0), IntTuple(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 8
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 0), IntTuple(3, 0), IntTuple(3, 1), IntTuple(3, 2),
                                 IntTuple(2, 2), IntTuple(1, 2), IntTuple(1, 1)])

    snake2 = Snake(True, IntTuple(0, 1), IntTuple(0, 3), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(0, 2), IntTuple(0, 3)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_RIGHT})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '  + + + ',
        '+ x   + ',
        '% % + + ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(1, 0), IntTuple(2, 0), IntTuple(3, 0), IntTuple(3, 1),
                                             IntTuple(3, 2), IntTuple(2, 2), IntTuple(1, 2)]
    assert new_snake1.length == 8
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(0, 1), IntTuple(0, 2)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_tail_chase_frontal_crash_grow():
    world, world_size = parse_world([
        '  @1*1*1',
        '@2$1  *1',
        '*2*1*1*1',
        '$2      ',
    ])
    snake1 = Snake(True, IntTuple(1, 0), IntTuple(1, 1), 1)
    snake1.grow = 1
    snake1.grow_uncertain = False
    snake1.length = 8
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 0), IntTuple(3, 0), IntTuple(3, 1), IntTuple(3, 2),
                                 IntTuple(2, 2), IntTuple(1, 2), IntTuple(1, 1)])

    snake2 = Snake(True, IntTuple(0, 1), IntTuple(0, 3), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(0, 2), IntTuple(0, 3)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_RIGHT})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '  x + + ',
        'x %   + ',
        '+ + + + ',
        '%       ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 0), IntTuple(3, 0), IntTuple(3, 1), IntTuple(3, 2),
                                             IntTuple(2, 2), IntTuple(1, 2), IntTuple(1, 1)]
    assert new_snake1.length == 8
    assert new_snake1.grow == 1
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(0, 2), IntTuple(0, 3)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain


def test_advance_game_double_body_kill():
    world, world_size = parse_world([
        '  @1*1$1',
        '$2*2@2  ',
        '        ',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(1, 0), IntTuple(3, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 0), IntTuple(3, 0)])

    snake2 = Snake(True, IntTuple(2, 1), IntTuple(0, 1), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(1, 1), IntTuple(0, 1)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '  x + % ',
        '  $2*2  ',
        '    @2  ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 0), IntTuple(3, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(2, 1), IntTuple(1, 1)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 1006
    assert not new_snake2.grow_uncertain


def test_advance_game_double_body_kill2():
    world, world_size = parse_world([
        '  @1*1$1',
        '*2@2    ',
        '$2      ',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(1, 0), IntTuple(3, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 0), IntTuple(3, 0)])

    snake2 = Snake(True, IntTuple(1, 1), IntTuple(0, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([IntTuple(0, 1), IntTuple(0, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_DOWN})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '  x + % ',
        '$2*2    ',
        '  @2    ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 0), IntTuple(3, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(1, 1), IntTuple(0, 1)]
    assert new_snake2.length == 3
    assert new_snake2.grow == 0
    assert new_snake2.score == 1006
    assert not new_snake2.grow_uncertain


def test_advance_game_double_mutual_body_kill():
    world, world_size = parse_world([
        '$1*1*1  ',
        '  @2@1  ',
        '  *2*2$2',
        '        ',
    ])
    snake1 = Snake(True, IntTuple(2, 1), IntTuple(0, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 4
    snake1.score = 4
    snake1.head_history = deque([IntTuple(2, 0), IntTuple(1, 0), IntTuple(0, 0)])

    snake2 = Snake(True, IntTuple(1, 1), IntTuple(3, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 4
    snake2.score = 6
    snake2.head_history = deque([IntTuple(1, 2), IntTuple(2, 2), IntTuple(3, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2})

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    new_state, uncertainty = robot.advance_game(game_state, {1: DIR_DOWN, 2: DIR_UP})

    assert not uncertainty
    assert serialize_world(new_state) == [
        '% + +   ',
        '  x x   ',
        '  + + % ',
        '        ',
    ]
    new_snake1 = new_state.snakes_by_color[1]
    assert not new_snake1.alive
    assert list(new_snake1.head_history) == [IntTuple(2, 0), IntTuple(1, 0), IntTuple(0, 0)]
    assert new_snake1.length == 4
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [IntTuple(1, 2), IntTuple(2, 2), IntTuple(3, 2)]
    assert new_snake2.length == 4
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain
