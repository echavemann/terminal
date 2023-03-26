import gamelib
import random
import math
import warnings
from sys import maxsize
import json


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.support_pos = [[7, 9], [8, 9], [9, 9], [5, 8], [8, 8], [9, 8], [10, 8], [6, 7], [9, 7], [10, 7], [11, 7], [7, 6], [10, 6], [11, 6], [12, 6], [8, 5], [11, 5], [12, 5], [13, 5], [9, 4], [12, 4], [13, 4], [10, 3], [13, 3], [14, 3], [15, 3], [11, 2], [14, 2], [15, 2], [16, 2], [12, 1], [15, 1], [13, 0]]
        self.support_pos = sorted(self.support_pos, key=lambda x: x[1])

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        for sup in self.support_pos:
            game_state.attempt_spawn(SUPPORT, sup, 1000)
                    
        if game_state.turn_number == 1:
            game_state.attempt_spawn(DEMOLISHER, [14, 0], 1)
            game_state.attempt_spawn(SCOUT, [14, 0], game_state.get_resource(MP))
        else:
            game_state.attempt_spawn(SCOUT, [14, 0], game_state.get_resource(MP))
        
        game_state.submit_turn()



    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        for sup in self.support_pos:
            game_state.attempt_spawn(SUPPORT, sup, 1000)
        
        if game_state.turn_number == 1:
            game_state.attempt_spawn(DEMOLISHER, [14, 0], 1)
            game_state.attempt_spawn(SCOUT, [14, 0], int(game_state.get_resource(MP)))
        else:
            game_state.attempt_spawn(SCOUT, [14, 0], int(game_state.get_resource(MP)))
        
        game_state.submit_turn()


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
