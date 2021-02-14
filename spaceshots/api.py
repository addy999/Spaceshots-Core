from .game import Game
from .scene import LevelBuilder
from random import randint

game = None
status = {}


def create_level_difficulties(max_difficulty: str, n_levels: int):

    _map = {0: "easy", 1: "medium", 2: "hard"}

    max_level = 2

    if max_difficulty == "medium":
        _map.pop(2)
        max_level = 1
    elif max_difficulty == "easy":
        _map.pop(2)
        _map.pop(1)
        max_level = 0

    # Now we all levels that we can possibly have, so let's create a distribution

    return [
        _map[randint(0, max_level)] if i > 0 else "easy" for i in range(n_levels)
    ]  # put easy first


def create_game(
    screen_x: float, screen_y: float, hardest_difficulty="hard", n_levels=5, fps=60
):

    global game
    global status

    builder = LevelBuilder(screen_x, screen_y)
    levels = [
        builder.create(diff)
        for diff in create_level_difficulties(hardest_difficulty, n_levels)
    ]
    game = Game(scenes=levels, fps=fps)
    status = {}


def step(thrust_dir) -> None:

    global game
    global status

    won, fail, message = game.step(thrust_dir)
    status = dict(won=won, fail=fail, message=message)
