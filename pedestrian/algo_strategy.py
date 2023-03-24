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

        ##########  defense features  ##########
        self.defense_queue = [] # a priority queue for building defense strcutures
        self.upgrade_queue = [] # a priority queue for upgrading defense structures
        self.spawn_locs = [[4, 9], [7, 6], [11, 2], [16, 2], [20, 6], [23, 9]] # the location where attacks are spawned
        self.defense_priority = { # dictionary that maps unit to priority, see bottom for more info
            'init_turret': 1,
            'init_ctr_wall': 2,
            'init_wall': 3,
            'extra_wall': 3,
            'extra_turret': 4,
        }
        self.upgrade_priority = { # dictionary that maps upgrades to priority, see bottom for more info
            'init_turret': 5,
            'init_wall': 6,
            'extra_turret': 7
        }
        self.extra_wall_locs = [(5,13), (5,12), (22,12), (22,13)] 
        self.side_wall_loc = [range(0, 5), range(23, 28)] 
        self.mid_wall_loc = [[9], [18], [13, 14]]
        self.turret_loc = [(3, 12),(24, 12),(13, 10),(9, 10),(18, 10)]
        self.walls_by_turret = [9, 13, 14, 18]

        ##########  offense features  ##########
        self.blocks = list(range(1, 39))
        self.block_threats = [0]*39
        self.block_locs = [
            [[4, 17], [5, 17], [4, 16], [5, 16]], # 1
            [[4, 14], [5, 14], [4, 15], [5, 15]], # 2

            [[6, 19], [7, 19], [6, 18], [7, 18]], # 3
            [[6, 17], [7, 17], [6, 16], [7, 16]], # 4
            [[6, 14], [7, 14], [6, 15], [7, 15]], # 5

            [[8, 21], [9, 21], [8, 20], [9, 20]], # 6
            [[8, 19], [9, 19], [8, 18], [9, 18]], # 7
            [[8, 17], [9, 17], [8, 16], [9, 16]], # 8
            [[8, 14], [9, 14], [8, 15], [9, 15]], # 9

            [[10, 22], [11, 22], [10, 23], [11, 23]], # 10
            [[10, 20], [11, 20], [10, 21], [11, 21]], # 11
            [[10, 18], [11, 18], [10, 19], [11, 19]], # 12
            [[10, 16], [11, 16], [10, 17], [11, 17]], # 13
            [[10, 14], [11, 14], [10, 15], [11, 15]], # 14

            [[12, 22], [13, 22], [12, 23], [13, 23]], # 15
            [[12, 20], [13, 20], [12, 21], [13, 21]], # 16
            [[12, 18], [13, 18], [12, 19], [13, 19]], # 17
            [[12, 16], [13, 16], [12, 17], [13, 17]], # 18
            [[12, 14], [13, 14], [12, 15], [13, 15]], # 19

            [[14, 22], [15, 22], [14, 23], [15, 23]], # 20
            [[14, 20], [15, 20], [14, 21], [15, 21]], # 21
            [[14, 18], [15, 18], [14, 19], [15, 19]], # 22
            [[14, 16], [15, 16], [14, 17], [15, 17]], # 23
            [[14, 14], [15, 14], [14, 15], [15, 15]], # 24

            [[16, 22], [17, 22], [16, 23], [17, 23]], # 25
            [[16, 20], [17, 20], [16, 21], [17, 21]], # 26
            [[16, 18], [17, 18], [16, 19], [17, 19]], # 27
            [[16, 16], [17, 16], [16, 17], [17, 17]], # 28
            [[16, 14], [17, 14], [16, 15], [17, 15]], # 29

            [[18, 21], [19, 21], [18, 20], [19, 20]], # 30
            [[18, 19], [19, 19], [18, 18], [19, 18]], # 31
            [[18, 17], [19, 17], [18, 16], [19, 16]], # 32
            [[18, 14], [19, 14], [18, 15], [19, 15]], # 33

            [[20, 19], [21, 19], [20, 18], [21, 18]], # 34
            [[20, 17], [21, 17], [20, 16], [21, 16]], # 35
            [[20, 14], [21, 14], [20, 15], [21, 15]], # 36

            [[22, 17], [23, 17], [22, 16], [23, 16]], # 37
            [[22, 14], [23, 14], [22, 15], [23, 15]], # 38
        ]
        self.spawn_locs = [[4, 9], [7, 6], [11, 2], [16, 2], [20, 6], [23, 9]] # the location where attacks are spawned
        self.path_lib = {
            0: [4, 5, 9, 14, 19, 8, 13, 12, 17, 18, 16, 22, 21, 20, 23, 26, 25, 27],
            1: [14, 18, 19, 22, 23, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35],
            2: [29, 32, 33, 34, 35, 36, 37, 38],
            3: [1, 2, 3, 4, 5, 8, 9, 14],
            4: [3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 17, 18, 19, 23, 24, 29],
            5: [6, 7, 10, 11, 12, 13, 15, 16, 17, 18, 19, 21, 22, 23, 24, 27, 28, 29, 32, 33, 36]
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
        self.handle_attack(game_state)
        self.refresh_defense(game_state)
        self.build_defense(game_state)
        game_state.submit_turn()
        self.turns += 1
    
    ##################################################################################
    """
    offense functions
    """

    def scan_threats(self, state):
        """
        scan the map for defense strength, update the block_threats every turn
        """
        for i in range(len(self.blocks)):
            block = self.blocks[i]
            threat = 0
            for loc in block:
                unit = state.contains_stationary_unit(loc)
                if unit:
                    threat += unit.damage_i * unit.health / unit.max_health
            self.block_threats[i] = threat

    def check_defense_strength(self, spawn_loc):
        """
        check the strength of the defense structures
        """
        path = self.path_lib[spawn_loc]
        threat = 0
        for block in path:
            threat += self.block_threats[block-1]
        return threat

    def get_attack_loc_by_threat(self, state):
        """
        check all possible spawn locations and return the one with the lowest threat
        """
        self.scan_threats(state)
        threats = [math.inf]*len(self.spawn_locs)
        for i in range(len(self.spawn_locs)):
            spawn_loc = self.spawn_locs[i]
            threats[i] = self.check_defense_strength(spawn_loc)
        min_threat = min(threats)
        return (threats.index(min_threat), min_threat)
    
    def handle_attack(self, state):
        """
        handle the attack
        """
        loc, threat = self.get_attack_loc_by_threat(state)
        mp = state.get_resource(MP)
        need_support = True
        if threat == 0: # no defense, spawn scouts
            self.spawn_attack(loc, 'scout', state)
            need_support = False # no need to build support cuz no defense
        elif mp >= 8 and threat <= 6: # one or less turret, spam scouts
            self.spawn_attack(loc, 'scout', state)
        elif mp >= 12 and threat <= 12: # two turret, demolishers with scouts
            self.spawn_attack(loc, 'demolisher', state)
        # elif mp >= 14 and threat > 12:  # demolishers with walls
        #     sp = state.get_resource(SP)
        #     if sp >= 3:
        #         self.spawn_attack(loc, 'demolisher_with_wall', state)
        #     else:
        #         attack = False
        else:
            need_support = False
        if need_support: # build support for attacks when high threat
            loc = (13, 9)
            pq.heappush(self.defense_queue, (0, [loc, SUPPORT]))
            pq.heappush(self.upgrade_queue, (0, loc))
        
    
    def spawn_attack(self, loc, mode, state):
        if mode == 'scout':
            state.attempt_spawn(SCOUT, loc, int(state.get_resource(MP)))
        elif mode == 'demolisher':
            state.attempt_spawn(DEMOLISHER, loc, 2)
            state.attempt_spawn(SCOUT, loc, int(state.get_resource(MP)))
    
    ##################################################################################
    """
    defense functions
    """

    def refresh_defense(self, state):
        """
        detect if any defense structures are destroyed and add them back to the queue
        """
        self.defense_queue = []

        # init turrets
        for turret_loc in self.turret_loc: # check turrets
            pq.heappush(self.defense_queue, (self.defense_priority['init_turret'], [turret_loc, TURRET]))

        for extra_wall_loc in self.extra_wall_locs:
            priority = self.defense_priority['init_wall']
            pq.heappush(self.defense_queue, (priority, [extra_wall_loc, WALL]))

        for walls in self.side_wall_loc: # check walls on the left and right
            for wall_loc in walls:
                priority = self.defense_priority['init_wall']
                if wall_loc in self.walls_by_turret: # walls that are right in front of main turrets
                    priority = self.defense_priority['init_ctr_wall']
                pq.heappush(self.defense_queue, (priority, [(wall_loc, 13), WALL]))

        # init and ctr walls
        for walls in self.mid_wall_loc: # check walls in the middle
            for wall_loc in walls:
                priority = self.defense_priority['init_wall']
                if wall_loc in [9, 13, 14, 18]: # walls that are right in front of main turrets
                    priority = self.defense_priority['init_ctr_wall']
                pq.heappush(self.defense_queue, (priority, [(wall_loc, 11), WALL]))  

        # extra turrets
        for turret_loc in [(4,12),(23,12),(14,10)]:
            if not state.contains_stationary_unit(turret_loc):
                priority = self.defense_priority['extra_turret']
                pq.heappush(self.defense_queue, (priority, [turret_loc, TURRET]))

        # check for turret upgrades, if not upgraded, add upgrades to the queue
        for turret_loc in self.turret_loc:
            unit = state.contains_stationary_unit(turret_loc)
            if unit and unit.upgraded == False:
                pq.heappush(self.upgrade_queue, (self.upgrade_priority['init_turret'], [turret_loc]))
        
        for extra_turret_loc in [(4,12),(23,12),(14,10)]: # extra turrets
            unit = state.contains_stationary_unit(extra_turret_loc)
            if unit and unit.upgraded == False:
                pq.heappush(self.upgrade_queue, (self.upgrade_priority['extra_turret'], [extra_turret_loc]))

        # check for wall upgrades, if not upgraded, add upgrades to the queue
        for walls in [range(0, 5), range(23, 28)]:
            for wall_loc in walls:
                wall_loc = [wall_loc, 13]
                unit = state.contains_stationary_unit(wall_loc)
                if unit and unit.upgraded == False:
                    pq.heappush(self.upgrade_queue, (self.upgrade_priority['init_wall'], wall_loc)) 
    
    def build_defense(self, state):
        """
        read in the defense queue and build defense by priority
        this func will always reserve sp for buildings walls for demolishers
        """        
        # build defense structures
        while self.defense_queue:
            _, (loc, unit) = pq.heappop(self.defense_queue)
            state.attempt_spawn(unit, loc)

        # upgrade defense structures
        while self.upgrade_queue:
            if state.get_resource(SP) < 5:
                _, loc = pq.heappop(self.upgrade_queue)
                state.attempt_upgrade(loc)

######################################################################################
"""
Defense priorities:
    init_turrets > init_walls > init_center_wall_upgrade > extra_turrets > 

Note: smaller number means higher priority
    Unit           Priority    Comments
 init turrets      (1)        # the 5 initial turrets
 init ctr walls    (2)        # the initial walls right front of the turrets 
 init walls        (3)        # other initial walls 
 extra turrets     (4)        # the bonus turrets

 support           (0)        # supports are usually not build until we start attacking

    Upgrade      Priority    Comments
1. turrets        (10)        # turrets are op
"""

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
