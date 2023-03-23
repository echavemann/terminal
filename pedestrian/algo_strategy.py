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
        self.spawn_loc = {"attack_right":[13, 0], "attack_left":[14, 0]} # the location where scouts are spawned
        self.defense_priority = { # dictionary that maps unit to priority, see bottom for more info
            'init_turret': 1,
            'init_ctr_wall': 2,
            'init_wall': 3,
            'extra_turret': 4,
            'extra_wall': 5
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
        strat = self.get_attack_side(game_state)
        if strat:
            side, mode = strat
            self.spawn_attack(side, mode, game_state)
        game_state.submit_turn()
        self.turns += 1

    ##################################################################################
    """
    offense functions
    """

    def check_defense_strength(self, state, spawn_loc):
        """
        check the strength of the defense structures
        """
        exptected_path = state.find_path_to_edge(spawn_loc, target_edge = state.get_target_edge(spawn_loc))
        threat = 0 # the total number of enemy structures that can attack the scouts on the path
        for loc in exptected_path:
            if loc[1] >= 12: # loop over all threatening units
                for unit in state.get_attackers(loc, 0):
                    distance = ((loc[0]-unit.x)**2+(loc[1]-unit.y)**2)**0.5
                    if distance <= 3.5:
                        discounter = unit.health / unit.max_health
                        threat += discounter * unit.damage_i
            else:
                continue # skip this loc because it's on our side
        return threat
    
    def get_attack_side(self, state):
        """
        organize the attack based on the strength of the defense
        """
        left_threat = self.check_defense_strength(state, self.spawn_loc['attack_left'])
        right_threat = self.check_defense_strength(state, self.spawn_loc['attack_right'])

        mp = state.get_resource(MP)
        if mp >= 5: 
            if left_threat > right_threat: # if left side is stronger, attack right
                side = 'attack_right' 
            else:
                side = 'attack_left'
            if left_threat < 20 or right_threat < 20: # if weak side exist, spam scouts
                mode = 'scout'
            elif mp > 10: # if we have enough mp, use demolishers and scouts
                """ do the demolisher attack"""
                mode = "demolisher"
            else:
                return None
        else:
            return None
        return [side, mode]
    
    def spawn_attack(self, side, mode, state):
        if mode == 'scout':
            spawn_loc = self.spawn_loc[side]
            state.attempt_spawn(SCOUT, spawn_loc, int(state.get_resource(MP)))
    
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

        gamelib.debug_write(len(self.defense_queue))
        # # check for wall upgrades, if not upgraded, add upgrades to the queue
        # for walls in [range(0, 5), range(23, 28)]:
        #     for wall_loc in walls:
        #         wall_loc = [wall_loc, 13]
        #         unit = state.contains_stationary_unit(wall_loc)
        #         if unit and unit.upgraded == False:
        #             pq.heappush(self.upgrade_queue, (self.upgrade_priority['init_wall'], [wall_loc, unit])) 
    
    def build_defense(self, state):
        """
        read in the defense queue and build defense by priority
        this func will always reserve sp for buildings walls for demolishers
        """        
        # build defense structures
        while self.defense_queue:
            _, (loc, unit) = pq.heappop(self.defense_queue)
            state.attempt_spawn(unit, loc)

        gamelib.util.debug_write(self.upgrade_queue)
        # upgrade defense structures
        # while self.upgrade_queue:
        #     _, (loc, unit) = pq.heappop(self.upgrade_queue)
        #     state.attempt_upgrade(loc)

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
