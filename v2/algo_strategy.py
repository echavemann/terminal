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
        self.side_walls = [[3, 11], [24, 11]]

                          # attack enemy right  attack enemy left
        self.spawn_locs =  [[13,0], [14, 0]]
        self.equivalent_locs = self.spawn_locs
        self.best_side = 0
        self.movement_tracks = {0: 0, 1: 0} # 0 if left, 1 if right
    
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

        self.fortside = max(self.movement_tracks, key=self.movement_tracks.get)
        
        if self.turns == 1: 
            self.build_initial(game_state)
            game_state.submit_turn()
            return
        self.run_it(game_state)
        
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        game_state.submit_turn()
        
    def handle_attack(self, game_state):
        """
        handles attack logic
        """
        mp = game_state.get_resource(MP)
        if mp > 8:
            game_state.attempt_spawn(SCOUT, self.spawn_locs[self.best_side], int(mp))
        
    def run_it(self, turn_state):
        self.build_defense(turn_state)
        self.handle_attack(turn_state)
        #insert attack logic here lmao

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
        moves = events["move"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                self.scored_on_locations.append(location)
        for move in moves:
            x, y = move[1]
            unit_owner_self = True if move[5] == 1 else False
            if y <= 15 and not unit_owner_self:
                if x < 14:
                    self.movement_tracks[0] += 1
                else:
                    self.movement_tracks[1] += 1
            
            
    ### ------------------- Turn Functions ------------------- ###

    
    def build_defense(self, game_state):
        """Builds our defensive structure - with side leaning."""
        #rebuild the initial defenses
        INITGUNS = [[1, 12], [26, 12], [4, 11]]
        INITWALLS = [[0, 13], [27, 13], [2, 12], [4, 12],[22, 12], [23, 12], [25, 12], [5, 11], [21, 11], [22, 11], [6, 10], [21, 10], [7, 9], [20, 9], [7, 8], [20, 8], [8, 7], [19, 7], [9, 6], [10, 6], [11, 6], [12, 6], [13, 6], [14, 6], [15, 6], [16, 6], [17, 6], [18, 6]]  
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
        #pick a side. 
        self.pick_side(game_state)
        if self.best_side == 0:
            self.select_right(game_state)
        else:
            self.select_left(game_state)
        #spawn symmetrical turret
        s = game_state.attempt_spawn(TURRET, [23, 11], 1)
        #Fortify a side. 
        #LHS Turret
        s = game_state.attempt_spawn(TURRET, [5, 10], 1)
        #RHS Wall Upgrades
        L1wallsRHS = [[22,12], [25, 12],[26, 13],[27,13]]
        for loca in L1wallsRHS:
            game_state.attempt_upgrade(loca)
        game_state.attempt_spawn(SUPPORT, [13, 5], 1)
        #RHS Turret
        s = game_state.attempt_spawn(TURRET, [22, 10], 1)
        #LHS Wall Upgrades
        L1wallsLHS = [[0,13],[1,13],[2,12],[4,12]]
        for loca in L1wallsLHS:
            game_state.attempt_upgrade(loca)
        #RHS Wall Upgrades
        L1wallsRHS = [[22,12], [25, 12],[26, 13],[27,13],[21,10]]
        for loca in L1wallsRHS:
            game_state.attempt_upgrade(loca)
        game_state.attempt_spawn(SUPPORT, [13, 5], 1)

        rhs = [[26,13],[27,13],[20, 8],[20,9],[21,10],[22,11],[23,12]]
        lhs = [[0, 13], [1,13],[2,12],[7,8],]# do wall upgrades 
        wall_upgrades = rhs + lhs
        for loca in wall_upgrades:
            game_state.attempt_upgrade(loca)
            if (s==1) : self.sp -= 1.5
        
        #spawn supports
        self.build_supports(game_state)

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

    ###-------------------- Helper Functions -------------------###
    def upkeep(self, turn_string):
        """Currently unused start of turn code."""
        game_state = gamelib.GameState(self.config, turn_string)
        self.turns += 1
        self.sp = game_state.get_resource(SP)
        self.mp = game_state.get_resource(MP)

    def compute_threat(self, game_state, spawn_loc):
        """
        computes the expected damage to receive if spawn at given loc
        """
        target_edge = game_state.get_target_edge(spawn_loc)
        
        path = game_state.find_path_to_edge(spawn_loc, target_edge)
        total_threat = 0
        
        for loc in path:
            threatening_turrets = game_state.get_attackers(loc, 0)
            for threatening_turret in threatening_turrets:
                total_threat += threatening_turret.damage_i * threatening_turret.health / threatening_turret.max_health
        return total_threat

    def pick_side(self, game_state):
        """
        the algo will take care of selecting side
        """
        sides = [0, 1]
        threats = [math.inf] * 2
        for side in sides:
            equivalent_locs = self.equivalent_locs[side]
            threat = self.compute_threat(game_state, equivalent_locs)
            threats[side] = threat

        min_threat = min(threats)
        self.best_side = threats.index(min_threat)
        
        gamelib.debug_write(f"   {threat}")

        gamelib.debug_write(f"  best side is {self.best_side} with threat {min_threat}")


    def build_supports(self, game_state):
        """Greedily build supports."""
        L1 = [[13, 5], [14, 5], [15, 5], [12, 5], [16, 5], [11, 5], [17, 5], [10, 5]] #good shit copilot lmao
        L2 = [[13, 4], [14, 4], [15, 4], [12, 4], [16, 4], [11, 4]]
        L3 = [[13, 3], [14, 3], [15, 3], [12, 3]]
        L4 = [[13, 2], [14, 2]]
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

    def select_left(self, game_state):
        # """Chooses the left side to attack on - builds a wall on the right. Requires 0.5SP."""
        game_state.attempt_spawn(WALL, [24, 11], 1)
        game_state.attempt_remove([24,11])

    def select_right(self, game_state):
        # """Chooses the right side to attack on - builds a wall on the left. Requires 0.5SP."""
        game_state.attempt_spawn(WALL, [3, 11], 1)
        game_state.attempt_remove([3,11])

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
