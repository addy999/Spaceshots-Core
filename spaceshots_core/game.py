import os, sys
import math
import numpy as np
import time

from .assests import *
from .scene import *
from .physics import *
     
class Game:
    
    def __init__(self, fps = 60.0, scenes = list):
        
        assert fps > 0, 'Game must have an FPS!'
        
        self.fps = fps
        self.dt = 1 / fps
        self.scenes = scenes    
        
        # Reset each scene
        self.reset()
    
    def control_sc(self, command=int):
        
        ''' 1: up, 2:left, 3: down, 4: right '''
            
        if command in [0,1,2,3,4]:
            
            if command != 0:
                self.current_scene.sc.thrust = True
                if command == 1:
                        self.current_scene.sc.thrust_direction = '+y'
                elif command == 2:
                        self.current_scene.sc.thrust_direction = '-x'
                elif command == 3:
                        self.current_scene.sc.thrust_direction = '-y'
                else: # command == 4
                        self.current_scene.sc.thrust_direction = '+x'
                    
            else: # release thrust
                self.current_scene.sc.thrust = False                
    
    def check_status(self):
        
        sc = self.current_scene.sc
        screen_x = self.current_scene.size[0]
        screen_y = self.current_scene.size[1]
        win_region_1 = self.current_scene.win_region[0]
        win_region_2 = self.current_scene.win_region[1]        
        won = False
        failed = False
        message = ""
        
                
        # Vertical
        if win_region_1[0] == win_region_2[0]: 
            if (win_region_1[0] == 0.0 and sc.x <= 0) or (win_region_1[0] == screen_x and sc.x >= screen_x):
                if win_region_1[1] <= sc.y <= win_region_2[1] and sc.vel.mag >= self.current_scene.win_min_velocity: 
                    won = True
                    message = "Won!"
                
        # Horizontal
        if win_region_1[1] == win_region_2[1]:
            if (win_region_1[1] == 0.0 and sc.y <= 0) or (win_region_1[1] == screen_y and sc.y >= screen_y):
                if win_region_1[0] <= sc.x <= win_region_2[0] and sc.vel.mag >= self.current_scene.win_min_velocity: 
                    won = True
                    message = "Won!"
                
        # Out of bounds
        if not won and (not 0.0 < sc.x < self.current_scene.size[0] or not 0.0 < sc.y < self.current_scene.size[1]):
            failed = True
            message = "Failed: Out of bounds."
        
        # Collisions
        if not failed:
            for planet in self.current_scene.planets:
                if sc.intersects(planet):
                    failed = True
                    message = "Failed: Collision."
        
        return won, failed, message
          
    def set_next_scene(self):
        
        if self.current_scene.won:
            
            current_i = self.scenes.index(self.current_scene)
            
            if current_i < len(self.scenes) - 1:
                self.current_scene = self.scenes[current_i+1]
            else:
                self.done = True
            
    def _scene_won(self):
        
        self.current_scene.won = True  
        self.current_scene.attempts += 1  
        self.set_next_scene()
        self.current_scene.reset_pos()              
    
    def _scene_failed(self):
        
        self.current_scene.reset_pos()
        self.current_scene.attempts += 1
    
    def calc_score(self):
        
        gas_bonus = 0.0        
        total = 0.0
        
        for scene in self.scenes:
            if scene.won:
                total += scene.completion_score 
                if scene.attempts > 1:
                    total -= (scene.attempts-1) * scene.attempt_score_reduction
                if scene.attempts >= 1:
                    gas_left = scene.sc.gas_level / scene.sc._initial_gas_level
                    gas_bonus += gas_left * scene.gas_bonus_score
                    total += gas_bonus            
        
        if total < 0:
            total = 0.0
            
        return total, gas_bonus            
    
    def reset(self):
        
        [s.reset() for s in self.scenes]
        self.current_scene = self.scenes[0]
        self.done = False  
    
    def wait(self, time_to_remove):
        
        dt = self.dt - time_to_remove
        if dt < 0:
            dt = 0
        
        time.sleep(dt)

    def step(self, command=int, wait=False):
        
        start = time.time()
        self.control_sc(command)
        self.current_scene.update_all_pos(self.dt)
        level_won, level_failed, message = self.check_status()
        
        if level_won:
            self._scene_won()
        elif level_failed:
            self._scene_failed()
        
        time_elapsed = time.time() - start
        
        if wait:
            self.wait(time_elapsed)
        
        return level_won, level_failed, message        
    
    def save_state(self):
        
        to_return = ""
        to_return += str(self.fps) + "+"
        
        
        
        