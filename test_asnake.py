from collections import deque
from typing import Tuple, List

from asnake import GameState, Snake, MyRobotSnake, DIR_DOWN, DIR_RIGHT, DIR_UP, GAME_CHARS, XY
from snakepit.robot_snake import World


def parse_world(lines: List[str]) -> Tuple[List[List[Tuple[str, int]]], XY]:
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
    return rows, XY(size_x, size_y)


REVERSE_CHARS = {v: k for k, v in GAME_CHARS.items()}


def serialize_world(state: GameState) -> List[str]:
    """Serialize world data to lines"""
    def describe(x, y):
        char, color = state.world_get(XY(x, y))

        return '{}{}'.format(REVERSE_CHARS[char], ' ' if color < 1 or color > 9 else str(color))
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
    ], XY(4, 4), {}, 0))
    assert lines == [
        '        ',
        '  $1*1@1',
        '        ',
        '        ',
    ]


def test_decode_encode():
    def check(value):
        assert value == GameState._decode_value(GameState._encode_value(value))

    for char in GAME_CHARS.values():
        for color in range(8):
            check((char, color))


def test_observe_state_changes_first():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '        ',
        '        ',
    ])

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    game_state = robot.observe_state_changes(None, robot.world, 1)

    assert game_state.world_size == XY(4, 4)
    my_snake = game_state.my_snake
    assert my_snake is not None
    assert my_snake.color == 1
    assert my_snake.length == 3
    assert list(my_snake.head_history) == [XY(2, 1), XY(1, 1)]
    assert my_snake.grow_uncertain
    assert my_snake.grow == 0
    assert my_snake.alive
    assert my_snake.score == 0
    assert my_snake.head_pos == XY(3, 1)
    assert my_snake.tail_pos == XY(1, 1)


def test_observe_state_changes_nontraceable():
    world, world_size = parse_world([
        '        ',
        '  @1*1*1',
        '  *1*1*1',
        '  *1*1$1',
    ])

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    game_state = robot.observe_state_changes(None, robot.world, 1)

    assert game_state.world_size == XY(4, 4)
    my_snake = game_state.my_snake
    assert my_snake is not None
    assert my_snake.color == 1
    assert my_snake.length == 9
    assert list(my_snake.head_history) == []
    assert my_snake.grow_uncertain
    assert my_snake.grow == 0
    assert my_snake.alive
    assert my_snake.score == 0
    assert my_snake.head_pos == XY(1, 1)
    assert my_snake.tail_pos == XY(3, 3)


def test_observe_state_changes_nontraceable2():
    world, world_size = parse_world([
        '@1*1    ',
        '  *1*1*1',
        '  *1*1*1',
        '  *1*1$1',
    ])

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    game_state = robot.observe_state_changes(None, robot.world, 1)

    assert game_state.world_size == XY(4, 4)
    my_snake = game_state.my_snake
    assert my_snake is not None
    assert my_snake.color == 1
    assert my_snake.length == 11
    assert list(my_snake.head_history) == [XY(1, 0), XY(1, 1)]
    assert my_snake.grow_uncertain
    assert my_snake.grow == 0
    assert my_snake.alive
    assert my_snake.score == 0
    assert my_snake.head_pos == XY(0, 0)
    assert my_snake.tail_pos == XY(3, 3)


def test_observe_state_changes_grow_uncertain():
    old_world, old_world_size = parse_world([
        '        ',
        '  $1*1@1',
        '        ',
        '        ',
    ])
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.length = 3
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    snake1.grow_uncertain = True
    snake1.grow = 1
    snake1.score = 5
    old_state = GameState(old_world, old_world_size, {1: snake1}, 0)

    world, world_size = parse_world([
        '        ',
        '  $1*1*1',
        '      @1',
        '        ',
    ])

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    game_state = robot.observe_state_changes(old_state, robot.world, 1)

    assert game_state.world_size == XY(4, 4)
    my_snake = game_state.my_snake
    assert my_snake is not None
    assert my_snake.color == 1
    assert my_snake.length == 4
    assert list(my_snake.head_history) == [XY(3, 1), XY(2, 1), XY(1, 1)]
    assert my_snake.grow_uncertain
    assert my_snake.grow == 0
    assert my_snake.alive
    assert my_snake.score == 5
    assert my_snake.head_pos == XY(3, 2)
    assert my_snake.tail_pos == XY(1, 1)


def test_observe_state_changes_stop_growing():
    old_world, old_world_size = parse_world([
        '        ',
        '  $1*1@1',
        '        ',
        '        ',
    ])
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.length = 3
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    snake1.grow_uncertain = True
    snake1.grow = 0
    snake1.score = 5
    old_state = GameState(old_world, old_world_size, {1: snake1}, 0)

    world, world_size = parse_world([
        '        ',
        '    $1*1',
        '      @1',
        '        ',
    ])

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    game_state = robot.observe_state_changes(old_state, robot.world, 1)

    assert game_state.world_size == XY(4, 4)
    my_snake = game_state.my_snake
    assert my_snake is not None
    assert my_snake.color == 1
    assert my_snake.head_pos == XY(3, 2)
    assert my_snake.tail_pos == XY(2, 1)
    assert my_snake.length == 3
    assert list(my_snake.head_history) == [XY(3, 1), XY(2, 1)]
    assert not my_snake.grow_uncertain
    assert my_snake.grow == 0
    assert my_snake.alive
    assert my_snake.score == 5


def test_observe_state_changes_eat():
    old_world, old_world_size = parse_world([
        '      84',
        '  $1*1@1',
        '        ',
        '        ',
    ])
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.length = 3
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    snake1.grow_uncertain = True
    snake1.grow = 0
    snake1.score = 5
    old_state = GameState(old_world, old_world_size, {1: snake1}, 0)

    world, world_size = parse_world([
        '      @1',
        '    $1*1',
        '        ',
        '        ',
    ])

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    game_state = robot.observe_state_changes(old_state, robot.world, 1)

    assert game_state.world_size == XY(4, 4)
    my_snake = game_state.my_snake
    assert my_snake is not None
    assert my_snake.color == 1
    assert my_snake.head_pos == XY(3, 0)
    assert my_snake.tail_pos == XY(2, 1)
    assert my_snake.length == 3
    assert list(my_snake.head_history) == [XY(3, 1), XY(2, 1)]
    assert not my_snake.grow_uncertain
    assert my_snake.grow == 8
    assert my_snake.alive
    assert my_snake.score == 13


def test_observe_state_changes_missed_frame():
    old_world, old_world_size = parse_world([
        '        ',
        '  $1*1@1',
        '        ',
        '        ',
    ])
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.length = 3
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    snake1.grow_uncertain = True
    snake1.grow = 0
    snake1.score = 5
    old_state = GameState(old_world, old_world_size, {1: snake1}, 0)

    world, world_size = parse_world([
        '        ',
        '      $1',
        '      *1',
        '      @1',
    ])

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    game_state = robot.observe_state_changes(old_state, robot.world, 1)

    assert game_state.world_size == XY(4, 4)
    my_snake = game_state.my_snake
    assert my_snake is not None
    assert my_snake.color == 1
    assert my_snake.head_pos == XY(3, 3)
    assert my_snake.tail_pos == XY(3, 1)
    assert my_snake.length == 3
    assert list(my_snake.head_history) == [XY(3, 2), XY(3, 1)]
    assert my_snake.grow_uncertain
    assert my_snake.grow == 0
    assert my_snake.alive
    assert my_snake.score == 5


def test_observe_state_changes_missed_frame2():
    old_world, old_world_size = parse_world([
        '        ',
        '  $1*1@1',
        '        ',
        '        ',
    ])
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.length = 3
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    snake1.grow_uncertain = True
    snake1.grow = 0
    snake1.score = 5
    old_state = GameState(old_world, old_world_size, {1: snake1}, 0)

    world, world_size = parse_world([
        '        ',
        '  $1*1*1',
        '      *1',
        '      @1',
    ])

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    game_state = robot.observe_state_changes(old_state, robot.world, 1)

    assert game_state.world_size == XY(4, 4)
    my_snake = game_state.my_snake
    assert my_snake is not None
    assert my_snake.color == 1
    assert my_snake.head_pos == XY(3, 3)
    assert my_snake.tail_pos == XY(1, 1)
    assert my_snake.length == 5
    assert list(my_snake.head_history) == [XY(3, 2), XY(3, 1), XY(2, 1), XY(1, 1)]
    assert my_snake.grow_uncertain
    assert my_snake.grow == 0
    assert my_snake.alive
    assert my_snake.score == 5


def test_observe_state_changes_appear():
    old_world, old_world_size = parse_world([
        '        ',
        '  $1*1@1',
        '        ',
        '        ',
    ])
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.length = 3
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    snake1.grow_uncertain = True
    snake1.grow = 1
    snake1.score = 5
    old_state = GameState(old_world, old_world_size, {1: snake1}, 0)

    world, world_size = parse_world([
        '$2      ',
        '*2$1*1*1',
        '@2    @1',
        '        ',
    ])

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    game_state = robot.observe_state_changes(old_state, robot.world, 1)

    assert game_state.world_size == XY(4, 4)
    my_snake = game_state.my_snake
    assert my_snake is not None
    assert my_snake.color == 1
    assert my_snake.length == 4
    assert list(my_snake.head_history) == [XY(3, 1), XY(2, 1), XY(1, 1)]
    assert my_snake.grow_uncertain
    assert my_snake.grow == 0
    assert my_snake.alive
    assert my_snake.score == 5
    assert my_snake.head_pos == XY(3, 2)
    assert my_snake.tail_pos == XY(1, 1)

    assert game_state.enemy_snake is not None
    assert game_state.enemy_snake.color == 2
    snake2 = game_state.snakes_by_color[2]
    assert snake2.color == 2
    assert snake2.length == 3
    assert list(snake2.head_history) == [XY(0, 1), XY(0, 0)]
    assert snake2.grow_uncertain
    assert snake2.grow == 0
    assert snake2.alive
    assert snake2.score == 0
    assert snake2.head_pos == XY(0, 2)
    assert snake2.tail_pos == XY(0, 0)


def test_observe_state_changes_die():
    old_world, old_world_size = parse_world([
        '$2      ',
        '*2$1*1@1',
        '@2      ',
        '        ',
    ])
    old_snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    old_snake1.length = 3
    old_snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    old_snake1.grow_uncertain = True
    old_snake1.grow = 1
    old_snake1.score = 5

    old_snake2 = Snake(True, XY(0, 2), XY(0, 0), 2)
    old_snake2.length = 3
    old_snake2.head_history = deque([XY(0, 1), XY(0, 0)])
    old_snake2.grow_uncertain = True
    old_snake2.grow = 0
    old_snake2.score = 9
    old_state = GameState(old_world, old_world_size, {1: old_snake1, 2: old_snake2}, 0)

    world, world_size = parse_world([
        '%       ',
        '+ $1*1*1',
        'x     @1',
        '        ',
    ])

    robot = MyRobotSnake(World(world_size.x, world_size.y, world))
    game_state = robot.observe_state_changes(old_state, robot.world, 1)

    assert game_state.world_size == XY(4, 4)
    my_snake = game_state.my_snake
    assert my_snake is not None
    assert my_snake.color == 1
    assert my_snake.length == 4
    assert list(my_snake.head_history) == [XY(3, 1), XY(2, 1), XY(1, 1)]
    assert my_snake.grow_uncertain
    assert my_snake.grow == 0
    assert my_snake.alive
    assert my_snake.score == 5
    assert my_snake.head_pos == XY(3, 2)
    assert my_snake.tail_pos == XY(1, 1)

    snake2 = game_state.snakes_by_color[2]
    assert not snake2.alive
    assert snake2.score == 9
    assert snake2.color == 2
    assert snake2.length == 3
    assert list(snake2.head_history) == [XY(0, 1), XY(0, 0)]
    assert snake2.grow_uncertain
    assert snake2.grow == 0
    assert snake2.head_pos == XY(0, 2)
    assert snake2.tail_pos == XY(0, 0)


def test_advance_game_simple_move():
    world, world_size = parse_world([
        '        ',
        '  $1*1@1',
        '        ',
        '        ',
    ])
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    game_state = GameState(world, world_size, {1: snake1}, 0)

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
    assert list(new_snake1.head_history) == [XY(3, 1), XY(2, 1)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 2
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    game_state = GameState(world, world_size, {1: snake1}, 0)

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
    assert list(new_snake1.head_history) == [XY(3, 1), XY(2, 1), XY(1, 1)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    game_state = GameState(world, world_size, {1: snake1}, 0)

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
    assert list(new_snake1.head_history) == [XY(3, 1), XY(2, 1)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 2
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    game_state = GameState(world, world_size, {1: snake1}, 0)

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
    assert list(new_snake1.head_history) == [XY(3, 1), XY(2, 1), XY(1, 1)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    game_state = GameState(world, world_size, {1: snake1}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 1), XY(1, 1)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    game_state = GameState(world, world_size, {1: snake1}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 1), XY(1, 1)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    game_state = GameState(world, world_size, {1: snake1}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 1), XY(1, 1)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])
    game_state = GameState(world, world_size, {1: snake1}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 1), XY(1, 1)]
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
    snake1 = Snake(True, XY(2, 2), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 5
    snake1.score = 4
    snake1.head_history = deque([XY(3, 2), XY(3, 1), XY(2, 1), XY(1, 1)])
    game_state = GameState(world, world_size, {1: snake1}, 0)

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
    assert list(new_snake1.head_history) == [XY(3, 2), XY(3, 1), XY(2, 1), XY(1, 1)]
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
    snake1 = Snake(True, XY(1, 2), XY(1, 1), 1)
    snake1.grow = 1
    snake1.grow_uncertain = False
    snake1.length = 6
    snake1.score = 4
    snake1.head_history = deque([XY(2, 2), XY(3, 2), XY(3, 1), XY(2, 1), XY(1, 1)])
    game_state = GameState(world, world_size, {1: snake1}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 2), XY(3, 2), XY(3, 1), XY(2, 1),
                                             XY(1, 1)]
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
    snake1 = Snake(True, XY(1, 2), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 6
    snake1.score = 4
    snake1.head_history = deque([XY(2, 2), XY(3, 2), XY(3, 1), XY(2, 1), XY(1, 1)])
    game_state = GameState(world, world_size, {1: snake1}, 0)

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
    assert list(new_snake1.head_history) == [XY(1, 2), XY(2, 2), XY(3, 2), XY(3, 1),
                                             XY(2, 1)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])

    snake2 = Snake(True, XY(3, 2), XY(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(3, 1), XY(2, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [XY(3, 2), XY(2, 2)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 2
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])

    snake2 = Snake(True, XY(3, 2), XY(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(3, 1), XY(2, 1), XY(1, 1)]
    assert new_snake1.length == 4
    assert new_snake1.grow == 1
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [XY(3, 2), XY(2, 2)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])

    snake2 = Snake(True, XY(3, 2), XY(1, 2), 2)
    snake2.grow = 1
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(3, 1), XY(2, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [XY(3, 2), XY(2, 2), XY(1, 2)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 2
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])

    snake2 = Snake(True, XY(3, 2), XY(1, 2), 2)
    snake2.grow = 1
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(3, 1), XY(2, 1), XY(1, 1)]
    assert new_snake1.length == 4
    assert new_snake1.grow == 1
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [XY(3, 2), XY(2, 2), XY(1, 2)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])

    snake2 = Snake(True, XY(2, 2), XY(0, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(1, 2), XY(0, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 1), XY(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(1, 2), XY(0, 2)]
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
    snake1 = Snake(True, XY(2, 1), XY(0, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(1, 1), XY(0, 1)])

    snake2 = Snake(True, XY(3, 2), XY(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(1, 1), XY(0, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(2, 2), XY(1, 2)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])

    snake2 = Snake(True, XY(1, 2), XY(0, 3), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(0, 2), XY(0, 3)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 1), XY(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(0, 2), XY(0, 3)]
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
    snake1 = Snake(True, XY(1, 1), XY(0, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(0, 1), XY(0, 0)])

    snake2 = Snake(True, XY(3, 2), XY(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(0, 1), XY(0, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(2, 2), XY(1, 2)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])

    snake2 = Snake(True, XY(3, 2), XY(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 1), XY(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(2, 2), XY(1, 2)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])

    snake2 = Snake(True, XY(3, 2), XY(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 1), XY(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(2, 2), XY(1, 2)]
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
    snake1 = Snake(True, XY(3, 1), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 1), XY(1, 1)])

    snake2 = Snake(True, XY(3, 2), XY(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 1), XY(1, 1)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(2, 2), XY(1, 2)]
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
    snake1 = Snake(True, XY(3, 2), XY(1, 2), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 2), XY(1, 2)])

    snake2 = Snake(True, XY(3, 1), XY(1, 1), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(2, 1), XY(1, 1)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 2), XY(1, 2)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(2, 1), XY(1, 1)]
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
    snake1 = Snake(True, XY(3, 0), XY(1, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 0), XY(1, 0)])

    snake2 = Snake(True, XY(3, 2), XY(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(3, 0), XY(2, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(3, 2), XY(2, 2)]
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
    snake1 = Snake(True, XY(3, 0), XY(1, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 0), XY(1, 0)])

    snake2 = Snake(True, XY(3, 2), XY(1, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(3, 0), XY(2, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(3, 2), XY(2, 2)]
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
    snake1 = Snake(True, XY(1, 0), XY(3, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 0), XY(3, 0)])

    snake2 = Snake(True, XY(3, 2), XY(1, 1), 2)
    snake2.grow = 1
    snake2.grow_uncertain = False
    snake2.length = 4
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2), XY(1, 1)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 0), XY(3, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [XY(3, 2), XY(2, 2), XY(1, 2), XY(1, 1)]
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
    snake1 = Snake(True, XY(1, 0), XY(3, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 0), XY(3, 0)])

    snake2 = Snake(True, XY(3, 2), XY(1, 1), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 4
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2), XY(1, 1)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(1, 0), XY(2, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [XY(3, 2), XY(2, 2), XY(1, 2)]
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
    snake1 = Snake(True, XY(1, 0), XY(3, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 4
    snake1.score = 4
    snake1.head_history = deque([XY(2, 0), XY(3, 0), XY(3, 1)])

    snake2 = Snake(True, XY(3, 2), XY(1, 1), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 4
    snake2.score = 6
    snake2.head_history = deque([XY(2, 2), XY(1, 2), XY(1, 1)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(1, 0), XY(2, 0), XY(3, 0)]
    assert new_snake1.length == 4
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [XY(3, 2), XY(2, 2), XY(1, 2)]
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
    snake1 = Snake(True, XY(1, 0), XY(1, 1), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 8
    snake1.score = 4
    snake1.head_history = deque([XY(2, 0), XY(3, 0), XY(3, 1), XY(3, 2),
                                 XY(2, 2), XY(1, 2), XY(1, 1)])

    snake2 = Snake(True, XY(0, 1), XY(0, 3), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(0, 2), XY(0, 3)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(1, 0), XY(2, 0), XY(3, 0), XY(3, 1),
                                             XY(3, 2), XY(2, 2), XY(1, 2)]
    assert new_snake1.length == 8
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(0, 1), XY(0, 2)]
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
    snake1 = Snake(True, XY(1, 0), XY(1, 1), 1)
    snake1.grow = 1
    snake1.grow_uncertain = False
    snake1.length = 8
    snake1.score = 4
    snake1.head_history = deque([XY(2, 0), XY(3, 0), XY(3, 1), XY(3, 2),
                                 XY(2, 2), XY(1, 2), XY(1, 1)])

    snake2 = Snake(True, XY(0, 1), XY(0, 3), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(0, 2), XY(0, 3)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 0), XY(3, 0), XY(3, 1), XY(3, 2),
                                             XY(2, 2), XY(1, 2), XY(1, 1)]
    assert new_snake1.length == 8
    assert new_snake1.grow == 1
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(0, 2), XY(0, 3)]
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
    snake1 = Snake(True, XY(1, 0), XY(3, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 0), XY(3, 0)])

    snake2 = Snake(True, XY(2, 1), XY(0, 1), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(1, 1), XY(0, 1)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 0), XY(3, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [XY(2, 1), XY(1, 1)]
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
    snake1 = Snake(True, XY(1, 0), XY(3, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 3
    snake1.score = 4
    snake1.head_history = deque([XY(2, 0), XY(3, 0)])

    snake2 = Snake(True, XY(1, 1), XY(0, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 3
    snake2.score = 6
    snake2.head_history = deque([XY(0, 1), XY(0, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 0), XY(3, 0)]
    assert new_snake1.length == 3
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert new_snake2.alive
    assert list(new_snake2.head_history) == [XY(1, 1), XY(0, 1)]
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
    snake1 = Snake(True, XY(2, 1), XY(0, 0), 1)
    snake1.grow = 0
    snake1.grow_uncertain = False
    snake1.length = 4
    snake1.score = 4
    snake1.head_history = deque([XY(2, 0), XY(1, 0), XY(0, 0)])

    snake2 = Snake(True, XY(1, 1), XY(3, 2), 2)
    snake2.grow = 0
    snake2.grow_uncertain = False
    snake2.length = 4
    snake2.score = 6
    snake2.head_history = deque([XY(1, 2), XY(2, 2), XY(3, 2)])

    game_state = GameState(world, world_size, {1: snake1, 2: snake2}, 0)

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
    assert list(new_snake1.head_history) == [XY(2, 0), XY(1, 0), XY(0, 0)]
    assert new_snake1.length == 4
    assert new_snake1.grow == 0
    assert new_snake1.score == 4
    assert not new_snake1.grow_uncertain

    new_snake2 = new_state.snakes_by_color[2]
    assert not new_snake2.alive
    assert list(new_snake2.head_history) == [XY(1, 2), XY(2, 2), XY(3, 2)]
    assert new_snake2.length == 4
    assert new_snake2.grow == 0
    assert new_snake2.score == 6
    assert not new_snake2.grow_uncertain
