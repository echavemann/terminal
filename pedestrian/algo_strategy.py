import gamelib
import random
import math
import warnings
from sys import maxsize
import json
import heapq as pq # priority queue


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
        self.turns = 1 # int that tracks turn number
        self.defense_queue = [] # a priority queue for building defense strcutures
        self.upgrade_queue = [] # a priority queue for upgrading defense structures
        self.reserved_sp = 0 # int that tracks the number of sp reserved for walls for demolishers
        self.defense_priority = { # dictionary that maps unit to priority, see bottom for more info
            'init_wall': 3,
            'init_turret': 1,
            'init_ctr_wall': 2,
            'extra_turret': 4,
            'extra_wall': 4
        }
        self.defense_build_cost = { # dictionary that maps unit to cost
            'wall': 0.5,
            'support': 4,
            'turret': 6,
        }
        self.defense_upgrade_cost = { # dictionary that maps upgrades to cost
            'wall': 1.5,
            'support': 2,
            'turret': 6,
        }
        self.upgrade_priority = { # dictionary that maps upgrades to priority, see bottom for more info
            'init_wall': 6,
            'init_turret': 5,
            'extra_turret': 7
        }

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
        self.refresh_defense(game_state)
        self.build_defense(game_state)
        game_state.submit_turn()
        self.turns += 1

    ##################################################################################
    """
    defense functions
    """

    def refresh_defense(self, state):
        """
        detect if any defense structures are destroyed and add them back to the queue
        """
        self.defense_queue = []

        # check if the initial defense structures are destroyed or not built, if so, add them back to the queue
        for turret_loc in [(3, 12),(24, 12),(13, 10),(9, 10),(18, 10)]: # check turrets
            if not state.contains_stationary_unit(turret_loc):
                pq.heappush(self.defense_queue, (self.defense_priority['init_turret'], [turret_loc, TURRET]))
        for walls in [range(0, 5), range(23, 28)]: # check walls on the left and right
            for wall_loc in walls:
                if not state.contains_stationary_unit((wall_loc, 13)):
                    priority = self.defense_priority['init_wall']
                    if wall_loc in [9, 13, 14, 18]: # walls that are right in front of main turrets
                        priority = self.defense_priority['init_ctr_wall']
                    pq.heappush(self.defense_queue, (priority, [(wall_loc, 13), WALL]))
        for walls in [range(12, 16), range(8, 11), range(17, 20)]: # check walls in the middle
            for wall_loc in walls:
                if not state.contains_stationary_unit((wall_loc, 11)):
                    priority = self.defense_priority['init_wall']
                    if wall_loc in [9, 13, 14, 18]: # walls that are right in front of main turrets
                        priority = self.defense_priority['init_ctr_wall']
                    pq.heappush(self.defense_queue, (priority, [(wall_loc, 11), WALL]))  

        for extra_wall_loc in [(5,13), (5,12), (22,12), (22,13)]:
            if not state.contains_stationary_unit(extra_wall_loc):
                priority = self.defense_priority['extra_wall']
                pq.heappush(self.defense_queue, (priority, [extra_wall_loc, WALL]))

        # check if the extra turrets are destroyed or not built, if so, add them back to the queue
        for turret_loc in [(4,12),(23,12),(14,10)]:
            if not state.contains_stationary_unit(turret_loc):
                priority = self.defense_priority['extra_turret']
                pq.heappush(self.defense_queue, (priority, [turret_loc, TURRET]))

        # # check for wall upgrades, if not upgraded, add upgrades to the queue
        # for walls in [range(0, 5), range(23, 28)]: # check if the center walls are upgraded
        #     for wall_loc in walls:
        #         unit = state.contains_stationary_unit((wall_loc, 13))
        #         if unit and unit.upgraded == False:
        #             pq.heappush(self.upgrade_queue, (self.upgrade_priority['init_wall'], (wall_loc, 13))) 
    
    def build_defense(self, state):
        """
        read in the defense queue and build defense by priority
        this func will always reserve sp for buildings walls for demolishers
        """
        sp = state.get_resource(SP)
        reserved_sp = 0
        if self.turns != 1: # if it is not the first turn, reserve sp for walls for demolishers
            reserved_sp = self.reserved_sp

        while self.defense_queue and sp >= reserved_sp:
            _, (loc, unit) = pq.heappop(self.defense_queue)
            if sp - state.type_cost(unit)[SP] >= reserved_sp:
                spawned = state.attempt_spawn(unit, loc)
                if spawned:
                    sp -= state.type_cost(unit)[SP]

        # while self.upgrade_queue and sp > reserved_sp:
        #     _, loc = pq.heappop(self.upgrade_queue)
        #     upgraded = state.attempt_upgrade(loc)
            # if upgraded:
            #     sp -= state.type_cost(upgrade)[SP]

######################################################################################
"""
defense priorities:
    init_turrets > init_walls > init_center_wall_upgrade > extra_turrets > 

    Unit           Priority    Comments
 init turrets      (15)        # the 5 initial turrets
 init ctr walls    (14)        # the initial walls right front of the turrets 
 init walls        (10)        # other initial walls 
 extra turrets     (13)        # the bonus turrets
 support           (20)        # supports are usually not build until we start attacking

    Upgrade      Priority    Comments
1. turrets       (10)        # turrets are op
"""

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
