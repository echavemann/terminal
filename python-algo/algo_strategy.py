import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        self.wallloc = [[0, 13], [1, 13], [4, 13], [27, 13], [6, 12], [6, 11], [25, 11], [6, 10], [24, 10], [23, 9], [7, 8], [9, 8], [10, 8], [11, 8], [12, 8], [13, 8], [14, 8], [15, 8], [16, 8], [17, 8], [18, 8], [19, 8], [20, 8], [21, 8], [22, 8]]
        self.buffloc = [[8, 7]]
        self.towerloc = [[2, 13], [3, 13], [26, 12], [5, 10], [6, 9]]
        self.workqueue = []
        self.workqueue.append(WALL, [0,13])
        rhs = [(WALL, [27,13]), (WALL, [25,11]), (WALL, [24,10]),(WALL, [23,9]),(WALL, [22,8]),(TURRET, [26,12])]
        lhs = [(WALL, [0,13]), (WALL, [1,13]), (WALL, [4,13]), (TURRET, [2,13]),(TURRET, [3,13]), (WALL, [6,12]), (WALL, [6,11]), (WALL, [6,10]), (TURRET, [5,10]), (TURRET, [6,9])]
        mhs = [(SUPPORT, [8,7]), (WALL, [9,8]), ((WALL, [10,8])), (WALL, [11,8]), (WALL, [12,8]), (WALL, [13,8]), (WALL, [14,8]), (WALL, [15,8]), (WALL, [16,8]), (WALL, [17,8]), (WALL, [19,8]), (WALL, [20,8]), (WALL, [21,8])]
        self.complete = rhs + lhs + mhs
        self.complete = True; #is True when the wall and buff are built so we can attack
        self.turns = 1;

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

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        if self.turns == 1:
            self.init_build(self, turn_state)
            game_state.submit_turn()
            return

        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.
        self.starter_strategy(game_state)
        game_state.submit_turn()

    def init_build(self, state):
        """
        Builds the initial wall layout. This is the same for every game.
        """
        wallloc = [[0, 13], [1, 13], [4, 13], [27, 13], [6, 12], [6, 11], [25, 11], [6, 10], [24, 10], [23, 9], [7, 8], [9, 8], [10, 8], [11, 8], [12, 8], [13, 8], [14, 8], [15, 8], [16, 8], [17, 8], [18, 8], [19, 8], [20, 8], [21, 8], [22, 8]]
        state.attempt_spawn(WALL, wallloc)
        buffloc = [[8, 7]]
        state.attempt_spawn(SUPPORT, buffloc)
        towerloc = [[2, 13], [3, 13], [26, 12], [5, 10], [6, 9]]
        state.attempt_spawn(TURRET, towerloc)

    def refresh_builds(self, state):
        sp = state.get_resource(SP)
        queue = self.workqueue
        while(sp >= 1):
            if(queue):
                item = queue.pop(0)
                if(item[0] == WALL):
                    state.attempt_spawn(WALL, item[1])
                    sp -= 1
                elif(item[0] == SUPPORT):
                    state.attempt_spawn(SUPPORT, item[1])
                    sp -= 4
                elif(item[0] == TURRET):
                    state.attempt_spawn(TURRET, item[1])
                    sp -= 2
            else:
                break
        self.complete = True
        if (sp >= 1):
            for item in self.workqueue:
                if (sp < 1): break
                if(item[0] == SUPPORT):
                    self.attempt_upgrade(SUPPORT, item[1])
                    sp -= 4
                elif(item[0] == WALL):
                    self.attempt_upgrade(WALL, item[1])
                    sp -= 1
                    #no turret upgrades for now
        return
        

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
