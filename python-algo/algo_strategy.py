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
        self.last_scored = True # if last turn attacked, record if all the scouts we sent scored

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
        self.wallloc = [[0, 13], [1, 13], [4, 13], [27, 13], [6, 12], [6, 11], [25, 11], [6, 10], [24, 10], [23, 9], [7, 8], [9, 8], [10, 8], [11, 8], [12, 8], [13, 8], [14, 8], [15, 8], [16, 8], [17, 8], [18, 8], [19, 8], [20, 8], [21, 8], [22, 8]]
        self.buffloc = [[8, 7]]
        self.towerloc = [[2, 13], [3, 13], [26, 12], [5, 10], [6, 9]]
        self.workqueue = []
        rhs = [(WALL, [27,13]), (WALL, [25,11]), (WALL, [24,10]),(WALL, [23,9]),(WALL, [22,8]),(TURRET, [26,12])]
        lhs = [(WALL, [0,13]), (WALL, [1,13]), (WALL, [4,13]), (TURRET, [2,13]),(TURRET, [3,13]), (WALL, [6,12]), (WALL, [6,11]), (WALL, [6,10]), (TURRET, [5,10]), (TURRET, [6,9])]
        mhs = [(SUPPORT, [8,7]),(WALL, [7,8]), (WALL, [9,8]), ((WALL, [10,8])), (WALL, [11,8]), (WALL, [12,8]), (WALL, [13,8]), (WALL, [14,8]), (WALL, [15,8]), (WALL, [16,8]), (WALL, [17,8]),(WALL, [18,8]), (WALL, [19,8]), (WALL, [20,8]), (WALL, [21,8])]
        self.workqueue = rhs + lhs + mhs
        self.complete = True; #is True when the wall and buff are built so we can attack
        self.turns = 1
        # This is a good place to do initial setup
        self.scored_on_locations = []
        
    def num_scouts_from_defense_strength(self, game_state):
        """
        Check if the defense on the attack path is strong
        return the number of scouts that we want to stack together
        
        -------
        input:
            game_state
        -------
        output:
            expected: number of scouts we expect to spawn for attack (int)
        """
        spawn_loc = [14, 0] # expect all attacks to be spawned at this place
        exptected_path = game_state.find_path_to_edge(spawn_loc, target_edge=game_state.get_target_edge(spawn_loc))
        threat = 0 # the total number of enemy structures that can attack the scouts on the path
        for loc in exptected_path:
            if loc[1] >= 12: # loop over all threatening units
                for unit in game_state.get_attackers(loc, 0):
                    distance = game_state.distance_between_locations(loc, [unit.x, unit.y])
                    if distance <= 3.5:
                        discounter = unit.health / unit.max_health
                        threat += discounter * unit.damage_i
            else:
                continue # skip this loc because it's on our side
        

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        self.refresh_builds(game_state)

        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.
        self.turns += 1
        
        # dummy offense logic
        # mp = game_state.MP()
        game_state.attempt_spawn(SCOUT,[14, 0],5)
        # gamelib.util.debug_write("attempt attack")
        
        game_state.submit_turn()

    def init_build(self, state):
        """
        Builds the initial wall layout. This is the same for every game.
        """
        for x in self.workqueue:
            state.attempt_spawn(x[0], x[1])

    def refresh_builds(self, state):
        self.complete = False
        sp = state.get_resource(SP)
        for item in self.workqueue:
            if sp < 1: return
            if(item[0] == SUPPORT and sp > 4):
                state.attempt_spawn(item[0], item[1])
                sp -= 4
            elif(item[0] == WALL and sp > 1):
                state.attempt_spawn(item[0], item[1])
                sp -= 1
            elif(item[0] == TURRET and sp > 2):
                state.attempt_spawn(item[0], item[1])
                sp -= 2
        self.complete = True
        for item in self.workqueue:
            if (sp < 1): return
            if(item[0] == SUPPORT and sp > 4):
                state.attempt_upgrade(item[1])
                sp -= 4
            elif(item[0] == WALL and sp > 1):
                state.attempt_upgrade(item[1])
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
