from deflectiun_core.game import *


def get_command(scene):
    return 0

sc = Spacecraft('', mass=1, width=1, length=1)
planets = []

game = Game()

while not game.done:
    
    command = get_command(game.current_scene)
    game.send_command(command) # iterate next time step
    game.check_status()
    
# if game.won:
    