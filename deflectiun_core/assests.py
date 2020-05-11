import sys
import os
import numpy as np
import math

from .physics import *
from .utils import * 
from shapely.geometry import Point, Polygon

class Asset:

    def __init__(self, name, x=0.0, y=0.0, mass=0, vel=None):

        self.x = x
        self.y = y
        self.name = name
        self.mass = mass
        self.vel = vel
        if not vel:
            self.vel = Velocity(0.0, 0.0)
            
        self.poly = None
        self._p = Momentum(self.vel.x, self.vel.y, self.mass)

    def reset_pos(self):

        self.x = 0
        self.y = 0

    def calc_distance(self, other_asset):

        dx = self.x - other_asset.x
        dy = self.y - other_asset.y

        return np.sqrt(dx**2 + dy**2)

    def calc_vector(self, other_asset):

        dx = other_asset.x - self.x
        dy = other_asset.y - self.y

        return dx, dy

    def calc_gravitational_force(self, other_asset):

        M = self.mass
        m = other_asset.mass
        r = self.calc_distance(other_asset)

        mag = G*M*m / r**2
        x, y = self.calc_vector(other_asset)

        return Force(x, y, mag)
    
    def intersects(self, other_asset):
        return self.poly.intersects(other_asset.poly)
    
    @property
    def p(self):
        return self._p

    @p.setter
    def p(self, val):
        self._p = val
        self.vel = Velocity(val.x / self.mass, val.y / self.mass)
    
    def __repr__(self):
        return str(vars(self))

class Planet(Asset):

    def __init__(self, 
                 name, 
                 mass=0.0, 
                 orbit=Orbit, 
                 radius_per_kilogram = 45 / 4e16):

        super().__init__(name, 0.0, 0.0, mass)
        self.orbit = orbit
        self.radius = radius_per_kilogram * mass
        self.move()
        self.poly = Point((self.x, self.y)).buffer(self.radius)

    def move(self, dt=1.0):

        self.x, self.y = self.orbit.next_pos(dt)
        self.poly = Point((self.x, self.y)).buffer(self.radius)
             
class Spacecraft(Asset):

    def __init__(self, name, mass=0.0, gas_level=0.0, thrust_force=0.0, width=10, length=10, gas_per_thrust=1/1000, min_dist_to_planet=1000):

        super().__init__(name, 0.0, 0.0, mass)
        self._theta = -math.pi/2
        self.gas_level = round_to_nearest(gas_level, 10)
        self._initial_gas_level = self.gas_level
        self.thrust = False
        self.thrust_direction = '-y'  # +/-x,-y
        self.thrust_mag = thrust_force
        self.width = width
        self.length = length
        self.gas_per_thrust = gas_per_thrust
        self.min_dist_to_planet = min_dist_to_planet
        self.draw_poly()

    def draw_poly(self):

        theta = self.theta
        
        # Initiate rectangle corners around origin
        rect = [
            (-self.width/2, -self.length/2),
            (+self.width/2, -self.length/2),
            (+self.width/2, +self.length/2),
            (-self.width/2, +self.length/2),
        ]
        
        # Rotate
        rotated_rect =  [rotate(theta, vec) for vec in rect]
        
        # Translate
        final_rect = [(p[0]+self.x, p[1]+self.y) for p in rotated_rect]
        
        self.coords = final_rect
        self.poly = Polygon(final_rect)        
    
    def get_thrust_impulse(self, time):

        if self.gas_level <= 0.0:
            self.gas_level = 0.0
            self.thrust = False

        if self.thrust:

            self.gas_level -= round(self.thrust_mag * self.gas_per_thrust)

            # body_vec = self.vel.vec
            body_vec = rotate(self.theta, [1,0])
            if np.linalg.norm(self.vel.vec) == 0.0:
                # body_vec = [0, -1]
                body_vec = [1, 0]

            if self.thrust_direction == '-y':
                vector = rotate(np.pi*1.5, body_vec)
            elif self.thrust_direction == '+y':
                vector = rotate(np.pi/2, body_vec)
            elif self.thrust_direction == '-x':
                vector = rotate(np.pi, body_vec)
            elif self.thrust_direction == '+x':
                vector = rotate(0.0, body_vec)

            force = Force(vector[0], vector[1], self.thrust_mag)
            return Momentum.from_impulse(force, time)

        return Momentum(0.0, 0.0)

    def set_net_momentum(self, impulse_time, external_force=None):

        # Thrust impulse
        thrust_i = self.get_thrust_impulse(impulse_time)

        # External impulse
        if external_force:
            external_i = Momentum.from_impulse(external_force, impulse_time)
        else:
            external_i = Momentum(0.0, 0.0)

        self.p = self.p + thrust_i + external_i

    def find_closest_planet(self, planets=list):

        current_distance = self.calc_distance(planets[0])
        # current_distance = self.min_dist_to_planet
        
        index_of_closest = 0
        current_index = 0
        for num in range(len(planets)):
            if self.calc_distance(planets[current_index]) < current_distance:
                index_of_closest = current_index
                current_distance = self.calc_distance(planets[current_index])
            current_index += 1
        
        # if current_distance == self.min_dist_to_planet:
        #     # No close planet found
        #     return None
        
        return planets[index_of_closest]

    def update_pos(self, impulse_time=float, planets=list, closest_only=True):

        planet_f = 0.0

        if closest_only:
            closes_planet = self.find_closest_planet(planets)
            if closes_planet:
                planet_f = self.calc_gravitational_force(closes_planet)
        else:
            for planet in planets:
                planet_f += self.calc_gravitational_force(planet)

        self.set_net_momentum(impulse_time, planet_f)
        self.move(impulse_time)

        return self.x, self.y
    
    def move(self, time):

        self.x += self.vel.x * time
        self.y += self.vel.y * time

    def reset(self, sc_start_pos=None):

        self.thrust = False
        if sc_start_pos:
            self.x, self.y = sc_start_pos
        self.p = Momentum(0.0, 0.0)
        self.gas_level = self._initial_gas_level

    @property
    def theta(self):
        return self._theta

    @theta.setter
    def theta(self, vel_theta):
               
        old_val = self._theta
        if abs(vel_theta-old_val) < math.pi:
            # self._theta = old_val + (val-old_val)/2
            self._theta = vel_theta - math.pi*0.5
        
    @property
    def p(self):
        return self._p

    @p.setter
    def p(self, val):
        self._p = val
        self.vel = Velocity(val.x / self.mass, val.y / self.mass)
        self.theta = self.vel.theta
        self.draw_poly()