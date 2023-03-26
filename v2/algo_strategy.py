import gamelib
import random
import math
import warnings
from sys import maxsize
import json
import heapq as pq

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
        self.scored_on_count = {'left':0, "right":0, "mid":0}
        self.defense_queue = []
        # This is a good place to do initial setup
        self.scored_on_locations = []

        #priority = 1-----------------------
        #initialize the map 
        self.init_turret_points = [[3, 12], [24, 12], [12, 8], [15, 8]]
        self.init_wall_points = [[0, 13], [1, 13], [2, 13], [3, 13], [4, 13], 
                            [23, 13], [24, 13], [25, 13], [26, 13], [27, 13], 
                            [4, 12], [23, 12], [4, 11], [23, 11], [5, 10], 
                            [22, 10], [6, 9], [10, 9], [11, 9], [12, 9], [15, 9], 
                            [16, 9], [17, 9], [21, 9], [7, 8], [10, 8], [17, 8],
                            [20, 8], [8, 7], [19, 7], [9, 6], [18, 6]]
        
        #priority = 2-----------------------
        #walls to build later
        self.later_wall_points = {0: [[13, 10], [14, 10], [10, 5], [17, 5]], 1: [[11, 5], [12, 5], [15, 5], [16, 5]], 2: [[12, 6], [15, 6]]}
        self.later_walls_built = 0
        

        #walls that should be upgraded
        self.wall_upgrades = [[3, 13], [4, 13], [23, 13], [24, 13], [4, 12], [23, 12],  #outsides
                            [10, 9], [11, 9], [16, 9], [17, 9], [10, 8], [17, 8], #middle
                            [12, 6], [15, 6], [11, 5], [12, 5], [15, 5], [16, 5]] #middle, lower
        #priority = 3-----------------------
        #upgrading turrets
        self.impt_turret_side = [[3, 12], [24, 12]]

        self.later_turret_points = [[11, 8], [16, 8]]

        #priority = 4-----------------------
        #upgrading turrets
        self.impt_turret_mid = [[12, 8], [15, 8]]

        # priority = 5
        #things that we dont really need
        self.last_turret_points = [[13, 2], [14, 2]]
        self.last_wall_points = [[12, 3], [15, 3]]
        self.impt_turret_mid_outer = [[11, 8], [16, 8]]
        
    def init_build(self, state:gamelib.GameState):
        """
        build initial defense
        """
        for loc in self.init_turret_points:
            pq.heappush(self.defense_queue, (1, [loc, TURRET]))
        for loc in self.init_wall_points:
            pq.heappush(self.defense_queue, (1.5, [loc, WALL]))
                
    def determine_priority(self):
        """
        determine which side we should prioritize according to the locs we have been scored on
        """
        self.priority = False
        if len(self.scored_on_locations) > 0:
            scored_on_side = max(self.scored_on_count, key=self.scored_on_count.get)
            count = self.scored_on_count[scored_on_side]
            self.priority = scored_on_side
    
    def apply_priority(self, loc):
        for i in range(len(self.defense_queue)):
            task = self.defense_queue[i]
            priority = task[0]
            loc = task[1][0]
            side = None
            if loc[0] < 5:
                side = "left"
            elif loc[0] > 22:
                side = "right"
            else:
                side = "mid"
            if self.priority and side == self.priority:
                self.defense_queue[i][0] -= 0.1

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
        
        self.determine_priority()
        # offense
        

        # defense
        self.defense_queue = []
        self.refresh_defense(game_state)
        self.process_defence_queue(game_state)
        game_state.submit_turn()
        
    def refresh_defense(self, game_state):
        sp = game_state.get_resource(SP)

        self.init_build(game_state) # makesure the foundation is not lost.

        for i in range(self.later_walls_built): #building the extra walls
            for loc in self.later_wall_points[i]:
                pq.heappush(self.defense_queue, (2, [loc, WALL]))

                sp -= 0.5
                if sp < 0.5: break
            if sp < 0.5: break
            
        if sp > 0.5:
            for x in range(self.later_walls_built, 3):
                self.later_walls_built += 1
                for loc in self.later_wall_points[x]:
                    pq.heappush(self.defense_queue, (2, [loc, WALL]))
                    sp -= 0.5
                    if sp < 0.5: break
                if sp < 0.5: break
        
        for wall in self.wall_upgrades:
            pq.heappush(self.defense_queue, (2, [wall, "upgrade"]))

        for turret in self.impt_turret_side:
            pq.heappush(self.defense_queue, (3, [turret, "upgrade"]))

        for loc in self.later_turret_points:
            pq.heappush(self.defense_queue, (3, [loc, TURRET]))

        for turret in self.impt_turret_mid:
            pq.heappush(self.defense_queue, (4, [turret, "upgrade"]))

        for x in self.last_wall_points:
            pq.heappush(self.defense_queue, (5, [x, WALL]))
            
        for turret in self.impt_turret_mid_outer:
            pq.heappush(self.defense_queue, (5, [turret, "upgrade"]))
            
        for x in self.last_turret_points:
            pq.heappush(self.defense_queue, (5, [x, TURRET]))
            
    def process_defence_queue(self, game_state):
        gamelib.debug_write("Defense Queue: {}".format(self.defense_queue))
        while len(self.defense_queue) > 0 and game_state.get_resource(SP) > 0:
            _, (task_loc, task_type) = pq.heappop(self.defense_queue)
            if task_type == "upgrade":
                game_state.attempt_upgrade(task_loc)
            else:
                game_state.attempt_spawn(task_type, task_loc)

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
                if location[0] <= 5:
                    self.scored_on_count['left'] += 1
                elif location[0] >= 22:
                    self.scored_on_count['right'] += 1
                else:
                    self.scored_on_count['mid'] += 1

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
