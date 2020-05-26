import numpy as np
import math
import os
import sys

from shapely.geometry.point import Point
import shapely.affinity

G = 6.67408e-11  # m^3/kg*s^2

class Velocity:

    def __init__(self, x_vel, y_vel):

        self.x = x_vel
        self.y = y_vel
        self.vec = [self.x, self.y]
        self.rot_matrix = get_rot_matrix(self.get_theta())
        self.mag = (self.x ** 2 + self.y ** 2) ** 0.5
        self.theta = self.get_theta()

    def get_theta(self):

        angle = angle_between([1, 0], self.vec)
        if self.y < 0:
            angle += np.pi

        return angle

    def save_state(self):
        
        return '+'.join(self.__dict__.values())

    def __repr__(self):       
         
        return str((self.x, self.y))

class Force:

    def __init__(self, x_vector, y_vector, mag):

        ratio, mag = self._create_ratio(x_vector, y_vector, mag)
        self.x = x_vector * ratio
        self.y = y_vector * ratio
        self.mag = mag
    
    def _create_ratio(self, x_vector, y_vector, mag):
        
        hyp = (x_vector ** 2 + y_vector ** 2) ** 0.5
        
        if hyp != 0.0:
            ratio = mag / hyp
        else:
            ratio = 0.0
            mag = 0.0
        
        return ratio, mag
    
    def save_state(self):
        
        return '+'.join(self.__dict__.values())
        
    def __add__(self, new):
        
        self.x += new.x
        self.y += new.y
        self.mag = (self.x ** 2 + self.y ** 2) ** 0.5
        
        return self
        
    def __repr__(self):

        return str((self.x, self.y))

class Momentum:

    def __init__(self, x_vel, y_vel, mass=1):

        self.x = mass * x_vel
        self.y = mass * y_vel

    @classmethod
    def from_impulse(cls, force=Force, duration=float):

        x = force.x * duration
        y = force.y * duration

        return cls(x, y)
    
    def save_state(self):
        
        return '+'.join(self.__dict__.values())

    def __add__(self, new):

        self.x += new.x
        self.y += new.y

        return self

    def __repr__(self):

        return str((self.x, self.y))

class Orbit:

    def __init__(self, a, b, center_x, center_y, progress=0.0, CW=True, angular_step=3.14/900):
        self.a = a
        self.b = b
        self.center_x = center_x
        self.center_y = center_y
        self.progress = progress
        self._ang_step = angular_step
        self.cw = CW
        
        self.make_poly(a, b, center_x, center_y)
        self.change_angular_step(angular_step)
    
    def make_poly(self, a, b, center_x, center_y):
        circ = shapely.geometry.Point((center_x, center_y)).buffer(1)
        ell  = shapely.affinity.scale(circ, int(a), int(b))
        self.poly = ell
    
    def change_angular_step(self, angular_step=float):
        self.angular_step = angular_step % 2*np.pi

    def x(self, progress):
        # i = progress
        # # return self.center_x - self.b * np.cos(i)    
        return self.a * np.cos(progress) + self.center_x

    def y(self, progress):
        # i = progress
        # return self.center_y + self.a * math.sin(i)       
        return self.b * np.sin(progress) + self.center_y

    def get_pos(self):
        return self.x(self.progress), self.y(self.progress)

    def next_pos(self, factor=1.0):
        
        if self.cw:
            self.progress += self.angular_step * factor
        else:
            self.progress -= self.angular_step * factor

        return self.get_pos()
    
    def save_state(self):
        
        return '+'.join(self.__dict__.values())

    def reset_pos(self):
        self.progress = 0
        return self.x(self.progress), self.y(self.progress)
    
    def __repr__(self):
        return str(vars(self))

class OrbitCollection:
    
    def __init__(self, orbits):
        
        self.orbits = orbits
    
    def orbits_valid(self, min_distance):
        for o in self.orbits:
            for j in self.orbits:
                if o!=j:                    
                    if o.poly.intersects(j.poly):
                        return False                    
                    if o.poly.exterior.distance(j.poly.exterior) < min_distance:
                        return False                
        return True

    def adjust_dir(self, screen_size):
        
        for o in self.orbits:
            pos = o.get_pos()
            if 0<=pos[0]<=screen_size[0]/2:
                o.cw = False
            else:
                o.cw = True

def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    if np.linalg.norm(vector) > 0:
        return vector / np.linalg.norm(vector)
    else:
        return np.array([0.0, 0.0])

def get_rot_matrix(theta):

    return [
        [math.cos(theta), -math.sin(theta)],
        [math.sin(theta), math.cos(theta)]
    ]

def rotate(theta, vec):
    
    return np.matmul(get_rot_matrix(theta), vec)

def angle_between(v1, v2):
    """ Returns the angle in degrees between vectors 'v1' and 'v2'::

            >>> angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            >>> angle_between((1, 0, 0), (1, 0, 0))
            0.0
            >>> angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))
