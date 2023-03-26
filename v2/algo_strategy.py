import gamelib
import random
import math
import warnings
from sys import maxsize
import json
import heapq as pq

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
        self.defense_queue = []
        self.scored_on_locations = []
        self.turns = 0
    
    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        self.turns += 1
        self.sp = game_state.get_resource(SP)
        self.mp = game_state.get_resource(MP)
        if self.turns == 1: 
            self.build_initial(game_state)
            game_state.submit_turn()
            return
        self.run_it(game_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        game_state.submit_turn()

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
                self.scored_on_locations.append(location)

    ###-------------------- Helper Functions -------------------###
    def upkeep(self, turn_string):
        game_state = gamelib.GameState(self.config, turn_string)
        self.turns += 1
        self.sp = game_state.get_resource(SP)
        self.mp = game_state.get_resource(MP)


    def build_supports(self, game_state):
        L1 = [[13, 5], [14, 5], [15, 5], [12, 5], [16, 5], [11, 5], [17, 5], [10, 5]] #good shit copilot lmao
        L2 = [[13, 4], [14, 4], [15, 4], [12, 4], [16, 4], [11, 4], [17, 4], [10, 4]]
        L3 = [[13, 3], [14, 3], [15, 3], [12, 3], [16, 3], [11, 3], [17, 3], [10, 3]]
        for loca in L1:
            s = game_state.attempt_spawn(SUPPORT, loca, 1)
            if (s==1) : self.sp -= 4
        if self.sp < 4: return
        for loca in L2:
            s = game_state.attempt_spawn(SUPPORT, loca, 1)
            if (s==1) : self.sp -= 4
        if self.sp < 4: return
        for loca in L3:
            s = game_state.attempt_spawn(SUPPORT, loca, 1)
            if (s==1) : self.sp -= 4

    def run_it(self, game_state):
        """core turn logic"""
        pass

    def select_left(self, game_state):
        """Chooses the left side to attack on - builds a wall on the right. Requires 0.5SP."""
        game_state.attempt_spawn(WALL, [24, 11], 1)
        game_state.attempt_remove([24,11])

    def select_right(self, game_state):
        """Chooses the right side to attack on - builds a wall on the left. Requires 0.5SP."""
        game_state.attempt_spawn(WALL, [3, 11], 1)
        game_state.attempt_remove([3,11])

    def build_initial(self, game_state):
        """Builds our initial defensive structure - with side leaning. """
        INITGUNS = [[1, 12], [26, 12], [4, 11]]
        INITWALLS = [[0, 13],[3,16], [27, 13], [2, 12], [4, 12],[22, 12], [23, 12], [25, 12], [5, 11], [21, 11], [22, 11], [6, 10], [21, 10], [7, 9], [20, 9], [7, 8], [20, 8], [8, 7], [19, 7], [9, 6], [10, 6], [11, 6], [12, 6], [13, 6], [14, 6], [15, 6], [16, 6], [17, 6], [18, 6]]  
        INITUWALLS = [[4, 12],[23, 12],[5,11],[22,11],[6,10]]   
        for loca in INITGUNS:
            s = game_state.attempt_spawn(TURRET, loca, 1)
            if (s==1) : self.sp -= 6
        for loca in INITWALLS:
            game_state.attempt_spawn(WALL, loca, 1)
            if (s==1) : self.sp -= 0.5
        for loca in INITUWALLS:
            game_state.attempt_upgrade(loca)
            if (s==1) : self.sp -= 1.5
        game_state.attempt_spawn(WALL, [24, 11], 1)
        game_state.attempt_remove([24,11])
        


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
