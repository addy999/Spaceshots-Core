import math

from .utils import *

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
        # if self.y < 0:
        #     angle += math.pi

        return angle

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

        return "+".join(self.__dict__.values())

    def __add__(self, new):

        self.x += new.x
        self.y += new.y

        return self

    def __repr__(self):

        return str((self.x, self.y))


class Orbit:
    def __init__(
        self, a, b, center_x, center_y, progress=0.0, CW=True, angular_step=3.14 / 900
    ):
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
        # circ = Point((center_x, center_y)).buffer(1)
        # poly  = shapely.affinity.scale(circ, int(a), int(b))
        self.poly = RectPolygon(
            [center_x - a, center_y + b],  # top left
            [center_x + a, center_y - b],  # bottom right
        )

    def change_angular_step(self, angular_step=float):
        self.angular_step = angular_step % 2 * math.pi

    def set_progress(self, pos):
        self.progress = math.acos((pos[0] - self.center_x) / self.a)

    def x(self, progress):
        # i = progress
        # # return self.center_x - self.b * math.cos(i)
        return self.a * math.cos(progress) + self.center_x

    def y(self, progress):
        # i = progress
        # return self.center_y + self.a * math.sin(i)
        return self.b * math.sin(progress) + self.center_y

    def get_pos(self):
        return self.x(self.progress), self.y(self.progress)

    def next_pos(self, factor=1.0):

        if self.cw:
            self.progress += self.angular_step * factor
        else:
            self.progress -= self.angular_step * factor

        return self.get_pos()

    def prev_pos(self, factor=1.0):
        self.next_pos(-factor)

    def reset_pos(self):
        self.progress = 0
        return self.x(self.progress), self.y(self.progress)

    def __repr__(self):
        return str(vars(self))


class OrbitCollection:
    def __init__(self, orbits):

        self.orbits = orbits

    def orbits_valid(self, min_distance, max_distance):
        for o in self.orbits:
            for j in self.orbits:
                if o != j:
                    if o.poly.intersects(j.poly):
                        return False

                    dist_between = o.poly.distance_to(j.poly)
                    if dist_between < min_distance or dist_between > max_distance:
                        return False
        return True

    def adjust_dir_to_sc(self, sc_pos):
        for o in self.orbits:
            current_dist = euclidian_distance(o.get_pos(), sc_pos)
            o.next_pos(5)
            next_dist = euclidian_distance(o.get_pos(), sc_pos)
            # print("sc", sc_pos, "Current", current_dist, "After",  next_dist)
            if next_dist > current_dist:
                # moved far away
                # print("changed")
                o.cw = not o.cw

    def adjust_dir_to_screen(self, x_screen, y_screen):
        center = (x_screen / 2, y_screen / 2)
        for o in self.orbits:
            current_dist = euclidian_distance(o.get_pos(), center)
            o.next_pos(1)
            next_dist = euclidian_distance(o.get_pos(), center)
            o.prev_pos(1)
            # print("center", center, "Current", current_dist, "After",  next_dist, o.cw)
            if next_dist > current_dist:
                # moved far away
                o.cw = not o.cw
            # print("now", o.cw)

    def adjust_cw_dir(self, screen_size):

        for o in self.orbits:
            x, y = o.get_pos()
            if x <= screen_size[0] / 2:
                o.cw = True
            else:
                o.cw = False


def distance_between_points(p1, p2) -> float:

    new_vec = [j - i for i, j in zip(p1, p2)]
    return vector_norm(new_vec)


class CirclePolygon:
    def __init__(self, center_x: float, center_y: float, r: float):

        self.x = center_x
        self.y = center_y
        self.r = r

    def intersects(self, other_poly) -> bool:

        if isinstance(other_poly, CirclePolygon):

            return (
                distance_between_points([self.x, self.y], [other_poly.x, other_poly.y])
                <= self.r + other_poly.r
            )


class RectPolygon:
    def __init__(self, tl: list, br: list) -> None:
        self.tl = tl
        self.br = br

    def intersects(self, other_rect):

        """
        Adapted from https://www.geeksforgeeks.org/find-two-rectangles-overlap/
        """

        if isinstance(other_rect, RectPolygon):

            # If one rectangle is on left side of other
            if self.tl[0] >= other_rect.br[0] or other_rect.tl[0] >= self.br[0]:
                return False

            # If one rectangle is above other
            if self.tl[1] <= other_rect.br[1] or other_rect.tl[1] <= self.br[1]:
                return False

            return True

    def distance_to(self, other_rect):

        """
        Adapted from https://stackoverflow.com/questions/4978323/how-to-calculate-distance-between-two-rectangles-context-a-game-in-lua
        """

        if isinstance(other_rect, RectPolygon):

            x1, y1, x1b, y1b = self.tl + self.br
            x2, y2, x2b, y2b = other_rect.tl + other_rect.br

            left = x2b < x1
            right = x1b < x2
            bottom = y2b < y1
            top = y1b < y2
            if top and left:
                return distance_between_points((x1, y1b), (x2b, y2))
            elif left and bottom:
                return distance_between_points((x1, y1), (x2b, y2b))
            elif bottom and right:
                return distance_between_points((x1b, y1), (x2, y2b))
            elif right and top:
                return distance_between_points((x1b, y1b), (x2, y2))
            elif left:
                return x1 - x2b
            elif right:
                return x2 - x1b
            elif bottom:
                return y1 - y2b
            elif top:
                return y2 - y1b
            else:  # rectangles intersect
                return 0.0


def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    norm = vector_norm(vector)
    if norm > 0:
        return [i / norm for i in vector]
    else:
        return [0.0, 0.0]


def get_rot_matrix(theta: float) -> list:

    return [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]]


def dot(v1: list, v2: list) -> float:
    """

    Args:
        v1 (list): n x 1 vector
        v2 (list): n x 1 vector

    Returns:
        float: dot product
    """

    return sum([i * j for i, j in zip(v1, v2)])


def matmul(X, Y):

    return [
        [sum(a * b for a, b in zip(X_row, Y_col)) for Y_col in zip(*Y)] for X_row in X
    ]


def rotate(theta, vec, custom=False):

    """
    Args:
    - theta: float
    - vec: list = 2 x 1 vector

    Returns:
        [type]: [description]
    """

    rot_matrix = get_rot_matrix(theta)  # 2 x 2
    return matmul(rot_matrix, vec)


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
    return math.acos(clip(dot(v1_u, v2_u), -1.0, 1.0))
