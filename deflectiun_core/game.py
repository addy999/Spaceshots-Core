import os, sys
import math
import numpy as np
import time
import ctypes

from .assests import *
from .scene import *
from .physics import *
     
class Game:
    
    def __init__(self, fps = 60.0, scenes = list):
        
        self.fps = fps
        self.last_dt = 1 / fps
        self.current_dt = 1 / fps
        self.scenes = scenes
        self.current_scene = self.scenes[0]
        self._done = False        
        
        # Reset each scene
        for scene in self.scenes:
            scene._attempts = 0
            scene.won = False
               
    def renderScene(self, scene):
        
        '''
        Render scene onto game screen
        '''
        
        # if pygame.display.get_surface().get_size() != scene.size:
        #     self.createScreen(scene)
            
        # background
        self.renderBackground(scene)
        
        # planets
        self.renderPlanets(scene)
        
        # win region
        self.renderWinRegion(scene)
        
        # spacecraft
        self.renderSc(scene)
        
        # Hu
        self.renderHud(scene)
    
    def renderHud(self, scene):
        
        sc = self.current_scene.sc
        
        # Gas level
        text_surface = self.font.render('Gas: ' + str(sc.gas_level), True, (255,255,255))
        self.screen.blit(text_surface, (0, scene.size[1]-20))
        
        # Velocity
        text_surface = self.font.render('Speed: ' + str(round(sc.vel.mag,2)), True, (255,255,255))
        self.screen.blit( text_surface, (scene.size[0]-130, scene.size[1]-50))
        
        # Escape velocity needed
        text_surface = self.font.render('Speed Required: ' + str(round(self.current_scene.win_min_velocity, 2)), True, (255,255,255))
        self.screen.blit(text_surface, (scene.size[0]-220, scene.size[1]-20))
        
        # Attempts
        text_surface = self.font.render('Attempts: ' + str(self.current_scene._attempts), True, (255,255,255))
        self.screen.blit(text_surface, (scene.size[0]-130, 10.0))
        
        # Level counter
        text_surface = self.font.render('Level ' + str(self.scenes.index(self.current_scene)+1), True, (255,255,255))
        self.screen.blit(text_surface, (scene.size[0]-130, 30))
    
    def captureSpacecraftControls(self, event):
            
        if event.type == pygame.KEYDOWN and event.key in [pygame.K_DOWN, pygame.K_UP, pygame.K_LEFT, pygame.K_RIGHT]:
            
            self.current_scene.sc.thrust = True
            if event.key == pygame.K_DOWN:
                    self.current_scene.sc.thrust_direction = '+y'
            if event.key == pygame.K_UP:
                    self.current_scene.sc.thrust_direction = '-y'
            if event.key == pygame.K_RIGHT:
                    self.current_scene.sc.thrust_direction = '-x'
            if event.key == pygame.K_LEFT:
                    self.current_scene.sc.thrust_direction = '+x'
        elif event.type == pygame.KEYUP and event.key in [pygame.K_DOWN, pygame.K_UP, pygame.K_LEFT, pygame.K_RIGHT]:
        
            self.current_scene.sc.thrust = False                
    
    def checkSceneWin(self, scene):
        
        sc = self.current_scene.sc
        screen_x = self.current_scene.size[0]
        screen_y = self.current_scene.size[0]
        win_region_1 = self.current_scene.win_region[0]
        win_region_2 = self.current_scene.win_region[1]
        
        won = False
        failed = False
        
        # Win if
        
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
            planet_r = self.__rpk*planet.mass
            if planet.x - planet_r <= sc.x <= planet.x + planet_r and planet.y - planet_r <= sc.y <= planet.y + planet_r:
                failed = True
        
        return won, failed
    
    def renderFullscreenDialog(self, texts, xoffsets = [], yoffsets = [], sleep_time = 1.5):
        
        screen_x = self.current_scene.size[0]
        screen_y = self.current_scene.size[1]
        self.screen.fill((0, 0, 0))
        c = 0
        
        if not xoffsets:
            [xoffsets.append(0) for i in range(len(texts))]
        if not yoffsets:
            [yoffsets.append(0) for i in range(len(texts))]
        
        for text in texts:
            text_surface = self.font.render(text, True, (255,255,255))
            self.screen.blit( text_surface, (screen_x/2 + xoffsets[c], screen_y/2 + yoffsets[c])) 
            c+=1 
            
        pygame.display.update()
        
        self.wait(sleep_time)
       
    def nextScene(self):
        
        current_i = self.scenes.index(self.current_scene)
        
        if current_i < len(self.scenes) - 1:
            self.current_scene  = self.scenes[current_i+1]
            return self.scenes[current_i+1]
        else:
            self._done = True
            return self.current_scene
    
    def gameWon(self):
        
        center_x = self.current_scene.size[0] / 2
        total_score, gas_bonus = self.calcScore()
            
        self.playAudio(getModpath() + r'\music\christmas.mp3')
        self.renderFullscreenDialog([
            'You\'re a gravity assist pro :D',
            '.......................',
            'Final score: ' + str(total_score),
            'including a gas bonus of ' + str(gas_bonus)
            ], 
            xoffsets = [-100, -30.0, -50.0, -100.0], yoffsets = [0, 50, 100, 130], sleep_time = 6.0)
        self.stopAudio()  
        
    def gameFail(self):
        
        total_score, gas_bonus = self.calcScore()
        self.playAudio(getModpath() + r'\music\christmas.mp3')
        center_x = self.current_scene.size[0] / 2 
        self.renderFullscreenDialog([
            'Quit! No worries, see ya next time!', 
            '.......................',
            'Final score: ' + str(total_score),
            'including a gas bonus of ' + str(gas_bonus)
            ], 
            xoffsets = [-130, -40.0, -50.0, -100.0], yoffsets = [0, 50, 100, 130],  sleep_time = 6.0)
        self.stopAudio()  
        
    def sceneWin(self):
        
        self.playAudio(getModpath() + r'\music\yeet_vine.mp3')        
        self.renderFullscreenDialog(['Won!'], xoffsets=[-10], sleep_time = 3.5)
        self.current_scene = self.nextScene() #iterate next scene
        self.current_scene.reset_pos()
        self.current_scene._attempts += 1
        self.current_scene.won = True    
        self.stopAudio()           
    
    def sceneFail(self):
        
        self.playAudio(getModpath() + r'\music\gottem_vine_cut.mp3')        
        self.renderFullscreenDialog(['Oops, try again!'], xoffsets=[-75], sleep_time = 3.5)
        self.current_scene.reset_pos()
        self.current_scene._attempts += 1
        self.stopAudio()   
    
    def calcScore(self):
        
        per_scene_score = 100.0
        attempt_deductions = 5.0
        gas_bonus_score = 10.0
        gas_bonus = 0.0        
        total = 0.0
        
        for scene in self.scenes:
            if scene.won:
                total += per_scene_score 
                if scene._attempts > 1:
                    total -= (scene._attempts-1) * attempt_deductions
                if scene._attempts >= 1:
                    gas_left = scene.sc.gas_level / scene.sc._initial_gas_level
                    gas_bonus += gas_left * gas_bonus_score
                    total += gas_bonus            
        
        if total < 0:
            total = 0.0
            
        # print('Winnings', [scene.won for scene in self.scenes])
        
        print('Total score', total)
                
        return total, gas_bonus            
    
    def startGame(self, scene_to_start_at = None, splash = True):
        
        self.createScreen(scene_to_start_at)
        # time.sleep(0.5)
        
        if splash:
            self.renderFullscreenDialog([
                'ASTRON', 
                'Use arrow keys (one at a time) to get to the green region with the required speed (bottom right)!'
                                        
            ], xoffsets = [-50, -400.0], yoffsets = [-20, 100], sleep_time= 7)

        self._done = False        
        while not self._done:
            
            # check game exit conditions
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self._done = True
                    
                # Modify spacecraft thrusters 
                self.captureSpacecraftControls(event)
                        
            # Iterate next planetary + sc positions
            self.current_scene.updateAllPos(self.current_dt)
                
            # Check scene exit conditions
            won, failed = self.checkSceneWin(self.current_scene)
            if won: self.sceneWin()
            elif failed: self.sceneFail()
    
            if not self._done:
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
        