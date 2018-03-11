Snake bot
==================================

The code tagged here as `v1.0.0` was used to run snake robot called `a` during
the [PyCon SK 2018 programming contest](https://github.com/pyconsk/snakepit-game).

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
export BOTPATH="$(pwd -P)/pyconsk-2018-snakepit-bot"
```

2. Install snakepit-game from https://github.com/pyconsk/snakepit-game

```
git clone https://github.com/pyconsk/snakepit-game
export GAMEPATH="${pwd -P}/snakepit-game"
cd "$GAMEPATH"
python3.6 -m venv env
source env/bin/activate
pip install -r doc/requirements.txt
export PYTHONPATH=$(pwd -P)
bin/run.py
```

3. Run `$GAMEPATH/bin/run_robot.py --code "$BOTPATH/asnake.py"`

Running tests
-------------

```
# setup venv
cd "$BOTPATH"
python3.6 -m venv env
source env/bin/activate
pip install -r requirements.txt

# run tests
py.test
```

Measuring performance
---------------------

There are several helper files (`bench.py` and `prof*.py`) that were used for measuring performance.

Running [timeit](https://docs.python.org/3/library/timeit.html):

```
python -m timeit -v -s 'import bench, asnake, time' 'bench.advance()'
python -m timeit -v -s 'import bench, asnake, time' 'bench.observe()'
python -m timeit -v -s 'import bench, asnake, time' 'bench.search()'
python -m timeit -v -s 'import bench, asnake, time' 'bench.bfs()'
```

Running [cProfile](https://docs.python.org/3/library/profile.html):

```
python -m cProfile -s time prof.py
python -m cProfile -s time prof2.py
python -m cProfile -s time prof3.py
python -m cProfile -s time prof4.py
```
