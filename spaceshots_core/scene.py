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
                #  sc_start_pos=None, 
                 win_region = tuple,
                 win_velocity = 0.0,
                 completion_score=100, 
                 attempt_score_reduction=5, 
                 gas_bonus_score=10,  
                 reset = True,
                 ):
        
        self.size = size
        self.sc = spacecraft
        self.planets = planets
        self.sc_start_pos = self.sc.x, self.sc.y 
        self.sc.min_dist_to_planet = min(*self.size)*0.75
        
        self.win_region = win_region
        self.win_min_velocity = round_to_nearest(win_velocity, 10)
        self.attempts = 0
        self.won = False
        self.fail = False
        
        self.completion_score = round_to_nearest(completion_score, 5)
        self.attempt_score_reduction = round_to_nearest(attempt_score_reduction, 5)
        self.gas_bonus_score = round_to_nearest(gas_bonus_score, 5)

        # if not self.sc_start_pos:
        #     self.sc_start_pos = self._set_sc_default_start_pos()
        # else:
        #     self.sc.x, self.sc.y = sc_start_pos

        self.initial_orbit_pos = [planet.orbit.progress for planet in planets]
        
        if reset:
            self.reset_pos()

    def _set_sc_default_start_pos(self):
        '''
        Default starting position assumed to be bottom centre of screen
        '''

        return self.size[0] / 2, self.sc.length/2

    def reset_pos(self):

        self.sc.reset(self.sc_start_pos)

        for i in range(len(self.planets)):
            self.planets[i].orbit.progress = self.initial_orbit_pos[i]
    
    def reset(self):
        
        self.reset_pos()
        self.attempts = 0
        self.won = False

    def update_all_pos(self, impulse_time):

        [planet.move(impulse_time) for planet in self.planets]
        self.sc.update_pos(impulse_time, self.planets, True)
    
    def save_state(self):
        
        return '+'.join(self.__dict__.values())
    
    def __repr__(self):
        pprint(str(vars(self)),width=100, indent=5,depth=4)
        return ''
       
class LevelBuilder:
    
    '''
    Generates spacecraft, planets, and scene based on some config options.
    '''
    def __init__(self, x_size, y_size, timeout=10):
        
        self.x_size = x_size
        self.y_size = y_size
        self.size = self.x_size * self.y_size
        self.diag = (self.x_size**2 + self.y_size**2)**0.5
        self.padding = min(x_size, y_size)/8
        self.timeout = timeout
        
        # Initialization dicts
        
        self.easy = dict(
            planet = dict(
                n = (1,1),
                mass = (3e16, 4e16),
            ),
            orbit = dict(
                a = (x_size/3, x_size/2),
                b = (y_size/3, y_size/2),
                angular_step = (2*np.pi/200, 2*np.pi/200), # speed
                center_x = (0, self.x_size), 
                center_y = (0, self.y_size/2),
            ),
            sc = dict(
                mass = (100, 125),
                gas_level = (350, 450),
                thrust_force = (3000,3000),
                size=(self.size*30/(942*539),self.size*35/(942*539)),
                start_pos=(
                    (self.x_size / 4, self.x_size * 0.75), 
                    (0, self.y_size*0.75)),
            ),
            scene = dict(
                win_region_length = sorted((self.x_size/2, self.y_size/2)), 
                win_region_pos_prob = [0.1, 0.8, 0.1],
                win_velocity = (90, 125),
                completion_score=(50,100), 
                attempt_score_reduction=(1,3), 
                gas_bonus_score=(5,5),  
            )   
        )
        self.medium = dict(
            planet = dict(
                n = (1,2),
                mass = (4e16, 5e16),
            ),
            orbit = dict(
                a = (x_size/4, x_size*0.75),
                b = (y_size/4, y_size*0.75),
                angular_step = (1.5*np.pi/200, 3*np.pi/200),
                center_x = (0, self.x_size), 
                center_y = (0, self.y_size),
            ),
            sc = dict(
                mass = (100, 125),
                gas_level = (300, 450),
                thrust_force = (3500,4500),
                size=(self.size*30/(942*539),self.size*35/(942*539)), 
                start_pos=(
                    (self.x_size / 4, self.x_size * 0.75), 
                    (0, self.y_size*0.75)),
            ),
            scene = dict(
                win_region_length = sorted((self.x_size/3, self.y_size/3)), 
                win_region_pos_prob = [1/3, 1/3, 1/3],
                win_velocity = (100, 150),
                completion_score=(100,150), 
                attempt_score_reduction=(5,7), 
                gas_bonus_score=(10,15),  
            )   
        )
    
    def generate_win_region(self, pos, length):
        
        ''' Randomly generate a win region. 0=left, 1=top, 2=right '''
        
        if pos == 0:
            p1 = [0, uniform(self.y_size/3, self.y_size*0.75)]
            p2 = [0, np.clip(p1[1] + length, None, self.y_size)]
        
        if pos == 1:
            p1 = [uniform(0, self.x_size/2), self.y_size]
            p2 = [np.clip(p1[0] + length, None, self.x_size), self.y_size]
        
        if pos == 2:
            p1 = [self.x_size, uniform(self.y_size/3, self.y_size*0.75)]
            p2 = [self.x_size, np.clip(p1[1] + length, None, self.y_size)]
        
        return p1,p2
    
    def move_planets(self, planets, sc):
        step = 2 * 1000/70
        iterations = 500
        for planet in planets:
            # Iterate planet positions 
            pos = [
                {   
                    "pos" : planet.move(step),
                    "sc_dist" : sc.calc_distance(planet),
                    "progress" : planet.orbit.progress
                }
                
                for i in range(iterations)
            ]
            # filter positions where planet is inside the screen - padding area 
            filtered_pos = [p for p in pos if self.padding<=p["pos"][0]<=self.x_size-self.padding and self.padding<=p["pos"][1]<=self.y_size-self.padding] 
            # Sort for largest distance away from sc 
            sorted_pos = sorted(filtered_pos, key = lambda i: i['sc_dist']) 
            # Set planet to furthest position
            planet.orbit.progress = sorted_pos[-1]["progress"]
            planet.x, planet.y = sorted_pos[-1]["pos"]
              
    def create(self, option):
        
        start = time.time()
        init_config = dict_to_class(self.__dict__[option.lower()])
        
        # Orbits      
        # print("Making orbits...")   
        orbits = []
        n = randint(*init_config.planet.n)
        orbits_valid = False
        dur = 0
        while not orbits_valid and dur<=self.timeout:
            s = time.time()
            orbits = OrbitCollection([Orbit(uniform(*init_config.orbit.a), uniform(*init_config.orbit.b), uniform(*init_config.orbit.center_x), uniform(*init_config.orbit.center_y), progress=uniform(0, 2*np.pi), angular_step=uniform(*init_config.orbit.angular_step)) for i in range(n)])
            orbits_valid = orbits.orbits_valid(uniform(self.x_size/2, self.y_size/2), uniform( self.diag/2, self.diag*0.75))
            dur += time.time() - s
        
        # SC
        # print("Making sc...")
        size = uniform(*init_config.sc.size)
        sc = Spacecraft('', uniform(*init_config.sc.mass), uniform(*init_config.sc.gas_level),uniform(*init_config.sc.thrust_force), width=size, length=size, x=uniform(*init_config.sc.start_pos[0]), y=np.clip(uniform(*init_config.sc.start_pos[1]), size/2, None))
                
        # Planets   
        # print("Making planets...")    
        planets = [Planet(name='', mass=uniform(*init_config.planet.mass), orbit = orbit) for orbit in orbits.orbits]
        min_distance_from_sc = self.diag / 3
        s = time.time()
        self.move_planets(planets, sc)
        print("Planets took", time.time() - s)
        
        # valid = False
        # dur = 0
        # while not valid and dur<=self.timeout:
        #     valid = True
        #     s = time.time()
        #     for planet in planets:
        #         if not self.padding<=planet.x<=self.x_size-self.padding or not self.padding<=planet.y<=self.y_size-self.padding or not sc.calc_distance(planet) > self.diag / 3:
        #             planet.move(10)
        #             valid = False
        #     dur += time.time() - s
            
        # Orbit directions
        orbits.adjust_dir_to_screen(self.x_size, self.y_size)
        # print([sc.calc_distance(planet) for planet in planets])
        # orbits.adjust_dir_to_sc(sc.pos()) 
  
        # Scene
        # print("Making scene...")
        win_region = self.generate_win_region(np.random.choice(range(0, 3), p=init_config.scene.win_region_pos_prob), uniform(*init_config.scene.win_region_length))
        scene = Scene((self.x_size,self.y_size), sc, planets, win_region=win_region, win_velocity=uniform(*init_config.scene.win_velocity), completion_score=randint(*init_config.scene.completion_score),attempt_score_reduction=randint(*init_config.scene.attempt_score_reduction ), gas_bonus_score=randint(*init_config.scene.gas_bonus_score))

        # print("Took", time.time() - start)
        return scene