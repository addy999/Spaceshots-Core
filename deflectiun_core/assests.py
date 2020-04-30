import sys
import os
import numpy as np
import math

from .physics import *
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

    def __init__(self, name, mass=0.0, gas_level=0.0, thrust_force=0.0, width=10, length=10):

        super().__init__(name, 0.0, 0.0, mass)
        self.gas_level = gas_level
        self._initial_gas_level = gas_level
        self.thrust = False
        self.thrust_direction = '-y'  # +/-x,-y
        self.thrust_mag = thrust_force
        self.width = width
        self.length = length
        self.draw_poly()

    def draw_poly(self):

        theta = self.vel.theta
        
        # Initiate rectangle corners around origin
        rect = [
            (-self.width/2, -self.length/2),
            (+self.width/2, -self.length/2),
            (+self.width/2, +self.length/2),
            (-self.width/2, +self.length/2),
        ]
        
        # Rotate
        rotated_rect =  [rotate(vec, theta) for vec in rect]
        
        # Translate
        final_rect = [(p[0]+self.x, p[1]+self.y) for p in rotated_rect]
        
        self.poly = Polygon(final_rect)        
    
    def body_transform(self, vector):
        ''' Body pointing towards self.vel '''

        return np.matmul(self.vel.rot_matrix, vector)

    def get_thrust_impulse(self, time):

        if self.gas_level <= 0.0:
            self.gas_level = 0.0
            self.thrust = False

        if self.thrust:

            self.gas_level -= self.thrust_mag / 1000

            vel_vec = self.vel.vec
            if np.linalg.norm(self.vel.vec) == 0.0:
                vel_vec = [0, -1]

            if self.thrust_direction == '-y':
                # vec = [0,-1]
                vector = vel_vec
            elif self.thrust_direction == '+y':
                # vec = [0,1]
                vector = np.matmul(get_rot_matrix(np.pi), vel_vec)
            elif self.thrust_direction == '-x':
                # vec = [1,0]
                vector = np.matmul(get_rot_matrix(np.pi/2), vel_vec)
            elif self.thrust_direction == '+x':
                # vec = [-1,0]
                vector = np.matmul(get_rot_matrix(np.pi * 1.5), vel_vec)

            force = Force(vector[0], vector[1], self.thrust_mag)
            # print(math.degrees(angle_between(self.vel.vec, [force.x,force.y])))
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
        index_of_closest = 0
        current_index = 0
        for num in range(len(planets)):
            if self.calc_distance(planets[current_index]) < current_distance:
                index_of_closest = current_index
                current_distance = self.calc_distance(planets[current_index])
            current_index += 1

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
    def p(self):
        return self._p

    @p.setter
    def p(self, val):
        self._p = val
        self.vel = Velocity(val.x / self.mass, val.y / self.mass)
        # print(val)