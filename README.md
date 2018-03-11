Snake bot
==================================

The code tagged here as `v1.0.0` was used to run snake robot called `a` during
the PyCon SK 2018 programming contest. 

Features:

- tracks game state such as movements of snakes, scores, frame rate
- searches for the direction of most food using breadth-first-search
- runs an iterative-deepening minimax search for selecting next move

Known bugs:

- tends to trap itself in a small space :)

Possible improvements:

- modify the BFS to find out whether next move will partition the space
  and try to avoid it if it does - this should make the snake not to trap itself
- use alpha-beta pruning or another pruning strategy to optimize the minimax search

Setup
-----

1. Clone this repository

```
git clone https://github.com/martin-sucha/pyconsk-2018-snakepit-bot
```

2. Install snakepit-game from https://github.com/pyconsk/snakepit-game
3. Run `./snakepit-game/bin/run_robot.py --code "pyconsk-2018-snakepit-bot/asnake.py"`

