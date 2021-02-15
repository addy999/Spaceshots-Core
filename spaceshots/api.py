from typing import Any
from .game import Game
from .scene import LevelBuilder
from random import randint


class Manager:
    def __init__(
        self,
        screen_x: float,
        screen_y: float,
        hardest_difficulty="hard",
        n_levels=5,
        fps=60,
    ):

        builder = LevelBuilder(screen_x, screen_y)
        levels = [
            builder.create(diff)
            for diff in create_level_difficulties(hardest_difficulty, n_levels)
        ]

        self.game = Game(scenes=levels, fps=fps)
        self.status = {}

    def get_details(self) -> dict:

        scene = self.game.current_scene
        length, width = scene.size

        data = {
            "sc": {
                # "mass" : round(scene.sc.mass,2),
                "pos": (round(scene.sc.x, 2), round(scene.sc.y, 2)),
                "speed": round(scene.sc.vel.mag),
                # "poly" : [[round(e,2) for e in i] for i in scene.sc.coords],
                "size": (scene.sc.width, scene.sc.length),
                "rot": round(scene.sc.theta, 2),
                "gas_level": scene.sc.gas_level,
                # "min_dist_to_planet" : round(scene.sc.min_dist_to_planet,2),
                # "gas_p_thrust" : scene.sc.gas_per_thrust,
                "i_gas_level": scene.sc._initial_gas_level,
                # "closest_dist_to_planet" : round(closest_dist_to_sc(scene.sc, scene.planets),1),
                # "p" : [scene.sc.p.x, scene.sc.p.y],
                "thrust": {
                    "mag": scene.sc.thrust_mag,
                    "dir": scene.sc.thrust_direction if scene.sc.thrust else "na",
                    "on": scene.sc.thrust,
                },
            }
        }

        data.update({"planets": []})
        for i, p in enumerate(scene.planets):
            p_data = {
                "pos": [round(i, 2) for i in (p.x, p.y)],
                # "mass" : round(p.mass,1),
                "radius": round(p.radius, 1),
                "orbit": {
                    "center": [
                        round(i, 1) for i in (p.orbit.center_x, p.orbit.center_y)
                    ],
                    "a": round(p.orbit.a, 1),
                    "b": round(p.orbit.b, 1),
                    # "cw" : p.orbit.cw,
                    # "ang_step" : p.orbit.angular_step,
                    # "progress" : round(p.orbit.progress,2)
                },
            }
            data["planets"].append(p_data)

        data.update(
            {
                "scene": {
                    "size": (length, width),
                    "win_region": [
                        [round(i, 1) for i in point] for point in scene.win_region
                    ],
                    "win_vel": scene.win_min_velocity,
                    "attempts": scene.attempts,
                    "completion_score": scene.completion_score,
                    "attempt_reduction": scene.attempt_score_reduction,
                    "gas_bonus": scene.gas_bonus_score,
                    # "init_orbits" : scene.initial_orbit_pos
                }
            }
        )

        return data

    def step(self, thrust_dir) -> None:

        won, fail, message = self.game.step(thrust_dir)
        self.status = dict(won=won, fail=fail, message=message)


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
