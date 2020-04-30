import os
import sys
import math
from .assests import *
from .physics import *

class Scene:

    def __init__(self, 
                 size, 
                 spacecraft, 
                 planets, 
                 sc_start_pos=None, 
                 win_region = tuple, # ([x1,x2], [y1,y2])
                 win_velocity = 0.0):

        self.size = size
        self.sc = spacecraft
        self.planets = planets
        self.sc_start_pos = sc_start_pos
        
        self.win_region = win_region
        self.win_min_velocity = win_velocity
        self._attempts = 0
        self.won = False

        if not self.sc_start_pos:
            self.sc_start_pos = self._make_sc_start_pos()
        else:
            self.sc.x, self.sc.y = sc_start_pos

        self.initial_orbit_pos = {}
        for planet in planets:
            self.initial_orbit_pos.update({
                planet: planet.orbit.progress
            })

        self.reset_pos()

    def _make_sc_start_pos(self):
        '''
        Default starting position assumed to be bottom centre of screen
        '''

        return self.size[0] / 2, self.size[1]-25

    def reset_pos(self):

        self.sc.reset(self.sc_start_pos)

        for planet in self.planets:
            planet.orbit.progress = self.initial_orbit_pos[planet]

    def update_all_pos(self, impulse_time):

        [planet.move(impulse_time) for planet in self.planets]
        self.sc.update_pos(impulse_time)