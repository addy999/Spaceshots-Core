import sys, os

sys.path.append("./")

print(os.path.abspath(sys.path[-1]))

from spaceshots.api import Manager


def test_basic_build():
    manage = Manager(500, 500)
    manage.step(0)  # no thrust
    manage.step(1)  # thrust
    manage.step(2)  # thrust
    manage.step(3)  # thrust
    manage.step(4)  # thrust
