import os, sys
import math
import numpy as np
import time
import ctypes

from .assests import *
from .scene import *
from .physics import *
     
class Game:
    
    def __init__(self, fps = 60.0, scenes = list, config = dict(
                per_scene_score = 100.0,
                per_attempt_deductions = 5.0,
                per_gas_bonus_score = 10.0)
                 ):
        
        self.fps = fps
        self.last_dt = 1 / fps
        self.current_dt = 1 / fps
        self.scenes = scenes    
        
        for c,k in config.items():
            self.__dict__.update({c,k})  
        
        # Reset each scene
        self.reset()
    
    def control_sc(self, command=int, pressed=True):
        
        ''' 1: up, 2:left, 3: down, 4: right '''
            
        if command in [1,2,3,4]:
            
            if pressed:
                self.current_scene.sc.thrust = True
                if command == 1:
                        self.current_scene.sc.thrust_direction = '+y'
                elif command == 2:
                        self.current_scene.sc.thrust_direction = '-y'
                elif command == 3:
                        self.current_scene.sc.thrust_direction = '-x'
                else:
                        self.current_scene.sc.thrust_direction = '+x'
                    
            else: # released
                self.current_scene.sc.thrust = False                
    
    def check_scene_win_fail(self, scene):
        
        sc = self.current_scene.sc
        screen_x = self.current_scene.size[0]
        screen_y = self.current_scene.size[0]
        win_region_1 = self.current_scene.win_region[0]
        win_region_2 = self.current_scene.win_region[1]
        
        won = False
        failed = False
                
        # vertical
        if win_region_1[0] == win_region_2[0] and win_region_1[0] == 0.0:
            # left half
            if sc.x <= 0 and win_region_1[1] <= sc.y <= win_region_2[1] and sc.vel.mag >= self.current_scene.win_min_velocity:
                won = True
        elif win_region_1[0] == win_region_2[0] and win_region_1[0] == screen_x:
            # right half
            if sc.x >= screen_x and win_region_1[1] <= sc.y <= win_region_2[1] and sc.vel.mag >= self.current_scene.win_min_velocity:
                won = True
        # Horizontal
        if win_region_1[1] == win_region_2[1] and win_region_1[1] == 0.0:
            # top half
            if sc.y <= 0 and win_region_1[0] <= sc.x <= win_region_2[0] and sc.vel.mag >= self.current_scene.win_min_velocity:
                won = True
        elif win_region_1[1] == win_region_2[1] and win_region_1[1] == screen_y:
            # bottom half
            if sc.y >= screen_y and win_region_1[0] <= sc.x <= win_region_2[0] and sc.vel.mag >= self.current_scene.win_min_velocity:
                won = True
                
        # Out of bounds
        if not won and (not 0.0 < sc.x < self.current_scene.size[0] or not 0.0 < sc.y < self.current_scene.size[1]):
            failed = True
        
        # Collisions
        for planet in self.current_scene.planets:
            if sc.intersects(planet):
                failed = True
        
        return won, failed
          
    def next_scene(self):
        
        current_i = self.scenes.index(self.current_scene)
        
        if current_i < len(self.scenes) - 1:
            self.current_scene  = self.scenes[current_i+1]
            return self.scenes[current_i+1]
        else:
            self.done = True
            return self.current_scene
            
    def win_scene(self):
        
        self.current_scene = self.next_scene() #iterate next scene
        self.current_scene.reset_pos()
        self.current_scene.attempts += 1
        self.current_scene.won = True    
    
    def fail_scene(self):
        
        self.current_scene.reset_pos()
        self.current_scene.attempts += 1
    
    def calc_score(self):
        
        gas_bonus = 0.0        
        total = 0.0
        
        for scene in self.scenes:
            if scene.won:
                total += per_scene_score 
                if scene.attempts > 1:
                    total -= (scene.attempts-1) * per_attempt_deductions
                if scene.attempts >= 1:
                    gas_left = scene.sc.gas_level / scene.sc._initial_gas_level
                    gas_bonus += gas_left * per_gas_bonus_score
                    total += gas_bonus            
        
        if total < 0:
            total = 0.0
            
        return total, gas_bonus            
    
    def reset(self):
        
        [s.reset() for s in self.scenes]
        self.current_scene = self.scenes[0]
        self.done = False  
   
    def start_game(self, scene_to_start_at = self.scenes[0]):
        
        self.done = False        
        while not self.done:
            
            # check game exit conditions
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.done = True
                    
                # Modify spacecraft thrusters 
                self.control_sc(event)
                        
            # Iterate next planetary + sc positions
            self.current_scene.updateAllPos(self.current_dt)
                
            # Check scene exit conditions
            won, failed = self.check_scene_win_fail(self.current_scene)
            if won: self.sceneWin()
            elif failed: self.fail_scene()
    
            if not self.done:
                # Draw modified scene            
                self.renderScene(self.current_scene)
                pygame.display.update()
                self.last_dt = self.current_dt
                self.current_dt = self.clock.tick(self.fps) / 1000 # to seconds
                if self.extra_time > 0.0 :
                    # Remove lag so game movements don't skip ahead
                    self.current_dt -= self.extra_time
                    self.extra_time = 0.0
        
                # print(self.last_dt, self.current_dt)

        if won:
            self.gameWon()
        else:
            self.gameFail()
    
        pygame.quit()
        