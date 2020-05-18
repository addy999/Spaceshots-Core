import os
import sys
import math
import time 

from numpy.random import uniform
from random import randint
from .assests import *
from .physics import *
from .utils import *

class Scene:

    def __init__(self, 
                 size, 
                 spacecraft, 
                 planets, 
                 sc_start_pos=None, 
                 win_region = tuple,
                 win_velocity = 0.0,
                 completion_score=100, 
                 attempt_score_reduction=5, 
                 gas_bonus_score=10,  
                 ):

        # # Save args
        # self.args = dict(
        #     size=size, 
        #     spacecraft=planets, 
        #     planets=planets, 
        #     sc_start_pos=sc_start_pos, 
        #     win_region = win_region,
        #     win_velocity = win_velocity,
        #     completion_score=completion_score, 
        #     attempt_score_reduction=attempt_score_reduction, 
        #     gas_bonus_score=gas_bonus_score,  
        # )        
        
        self.size = size
        self.sc = spacecraft
        self.planets = planets
        self.sc_start_pos = sc_start_pos
        self.sc.min_dist_to_planet = min(*self.size)*0.75
        
        self.win_region = win_region
        self.win_min_velocity = round_to_nearest(win_velocity, 10)
        self.attempts = 0
        self.won = False
        self.fail = False
        
        self.completion_score = round_to_nearest(completion_score, 5)
        self.attempt_score_reduction = round_to_nearest(attempt_score_reduction, 5)
        self.gas_bonus_score = round_to_nearest(gas_bonus_score, 5)

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

        return self.size[0] / 2, self.sc.length/2

    def reset_pos(self):

        self.sc.reset(self.sc_start_pos)

        for planet in self.planets:
            planet.orbit.progress = self.initial_orbit_pos[planet]
    
    def reset(self):
        
        self.reset_pos()
        self.attempts = 0
        self.won = False

    def update_all_pos(self, impulse_time):

        [planet.move(impulse_time) for planet in self.planets]
        self.sc.update_pos(impulse_time, self.planets, False)
    
    def save_state(self):
        
        return '+'.join(self.__dict__.values())
    
    def __repr__(self):
        pprint(str(vars(self)),width=100, indent=5,depth=4)
        return ''
       
class LevelBuilder:
    
    '''
    Generates spacecraft, planets, and scene based on some config options.
    '''
    def __init__(self, x_size, y_size):
        
        self.x_size = x_size
        self.y_size = y_size
        
        # Initialization dicts
        
        self.easy = dict(
            planet = dict(
                n = (1,1),
                mass = (3e16, 4e16),
                radius_per_kilogram = (45 / 4e16, 45 / 4e16)
            ),
            orbit = dict(
                a = (300, 400), # 324
                b = (200, 300), # 234
                angular_step = (2*np.pi/200, 2*np.pi/200), # speed
                center_x = (0, self.x_size), 
                center_y = (0, self.y_size),
                min_distance = (self.x_size/2, self.y_size/2),
            ),
            sc = dict(
                mass = (100, 125),
                gas_level = (500, 600),
                thrust_force = (3000,3000),
                gas_per_thrust = (0.5/1000, 1/1000),
                width=(35,35), 
                length=(35,35),
            ),
            scene = dict(
                win_region1 = ((0, self.x_size/4), (self.y_size,self.y_size)),
                win_region2 = ((self.x_size*0.75, self.x_size), (self.y_size,self.y_size)), 
                win_velocity = (90, 150),
                completion_score=(50,100), 
                attempt_score_reduction=(1,3), 
                gas_bonus_score=(5,5),  
            )   
        )
        self.medium = dict(
            planet = dict(
                n = (1,2),
                mass = (4e16, 5e16),
                radius_per_kilogram = (45 / 4e16, 45 / 4e16)
            ),
            orbit = dict(
                progress = (-np.pi/2, np.pi/2),
                a = (100, 500),
                b = (300, 600),
                angular_step = (1.5*np.pi/200, 3*np.pi/200), # speed
                center_x = (0, self.x_size), 
                center_y = (0, self.y_size),
                min_distance = (self.x_size/2, self.y_size/2),
            ),
            sc = dict(
                mass = (100, 125),
                gas_level = (350, 450),
                thrust_force = (3000,4500),
                gas_per_thrust = (1/1000, 1.5/1000),
                width=(35,35), 
                length=(35,35),
            ),
            scene = dict(
                win_region1 = ((0,0), (self.y_size/3, self.y_size/2)), 
                win_region2 = ((0,0), (self.y_size*0.75,self.y_size)), 
                win_velocity = (150, 190),
                completion_score=(100,150), 
                attempt_score_reduction=(5,7), 
                gas_bonus_score=(10,15),  
            )   
        )
    
    def create(self, option='medium'):
        # start=time.time()       
        init_config = dict_to_class(self.__dict__[option.lower()])
        
        # Orbits         
        orbits = []
        n = randint(*init_config.planet.n)
        valid_orbits = False
        while not valid_orbits:
            orbits = [Orbit(uniform(*init_config.orbit.a), uniform(*init_config.orbit.b), uniform(*init_config.orbit.center_x), uniform(*init_config.orbit.center_y), angular_step=uniform(*init_config.orbit.angular_step), CW=randint(0,1)) for i in range(n)]
            valid_orbits = OrbitCollection(orbits, uniform(*init_config.orbit.min_distance)).orbits_valid()
        
         # SC
        sc = Spacecraft('', uniform(*init_config.sc.mass), uniform(*init_config.sc.gas_level),uniform(*init_config.sc.thrust_force), gas_per_thrust=uniform(*init_config.sc.gas_per_thrust), width=uniform(*init_config.sc.width), length=uniform(*init_config.sc.length))
        
        # Planets    
        planets = [Planet(name='', mass=uniform(*init_config.planet.mass), orbit = orbit, radius_per_kilogram=uniform(*init_config.planet.radius_per_kilogram)) for orbit in orbits]
        valid = False
        while not valid:
            valid = True
            for planet in planets:
                if not 0<=planet.x<=self.x_size or not 0<=planet.y<=self.y_size or sc.calc_distance(planet) < self.y_size/2:
                    planet.move(10)
                    valid = False
  
        # Scene
        win_region1 = (uniform(*init_config.scene.win_region1[0]), uniform(*init_config.scene.win_region1[1]))    
        win_region2 = (uniform(*init_config.scene.win_region2[0]), uniform(*init_config.scene.win_region2[1]))    
        scene = Scene((self.x_size,self.y_size), sc, planets, sc_start_pos=None, win_region=(win_region1, win_region2), win_velocity=uniform(*init_config.scene.win_velocity), completion_score=randint(*init_config.scene.completion_score),attempt_score_reduction=randint(*init_config.scene.attempt_score_reduction ), gas_bonus_score=randint(*init_config.scene.gas_bonus_score))
        
        # print("TIME TAKEN", time.time()-start)
        return scene