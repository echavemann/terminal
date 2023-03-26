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
        self.enemy_interceptors = []
        self.scored_on_locations = []
        self.turns = 0
        self.sup_count = 0
        self.side_walls = [[5, 8], [22, 8]]
        self.enemy_attack_thresholds = []
        self.last_turn = math.inf
        self.fight_beta = False
                          # attack enemy right  attack enemy left
        self.spawn_locs =  [[4, 9], [23, 9]]
        self.equivalent_locs = self.spawn_locs
        self.best_side = 0
        self.movement_tracks = {0: 0, 1: 0} # 0 if left, 1 if right
        self.enemy_weak_side = False # false if no exploitable side, 0 if left, 1 if right
        self.enemy_left_side = [[0, 13], [1, 13], [2, 13], [3, 13], [4, 13], [5, 13], [6, 13], [7, 13], [1, 12], [2, 12], [3, 12], [4, 12], [5, 12], [6, 12], [7, 12], [2, 11], [3, 11], [4, 11], [5, 11], [6, 11], [7, 11], [3, 10], [4, 10], [5, 10], [6, 10], [7, 10], [4, 9], [5, 9], [6, 9], [7, 9], [5, 8], [6, 8], [7, 8], [6, 7], [7, 7], [7, 6]]
        self.enemy_right_side = [[20, 13], [21, 13], [22, 13], [23, 13], [24, 13], [25, 13], [26, 13], [27, 13], [20, 12], [21, 12], [22, 12], [23, 12], [24, 12], [25, 12], [26, 12], [20, 11], [21, 11], [22, 11], [23, 11], [24, 11], [25, 11], [20, 10], [21, 10], [22, 10], [23, 10], [24, 10], [20, 9], [21, 9], [22, 9], [23, 9], [20, 8], [21, 8], [22, 8], [20, 7], [21, 7], [20, 6]]
        self.enemysides = [self.enemy_left_side, self.enemy_right_side]
        self.score = []
        self.expectation = [0]
        self.ehp = 30
    
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
        self.min_threat = math.inf
        self.enemy_weak_side = False
        self.sp = game_state.get_resource(SP)
        self.mp = game_state.get_resource(MP)
        self.scan_side(game_state)
        self.paths = []
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
        if not self.enemy_weak_side:
            # regular attack logic
            self.attack_v2(game_state)
        else: # handle enemy weak side exploit
            side, count = self.enemy_weak_side
            count = max(1, count)
            if mp >= count * 3 + 1: # if have enough mp for spawning scouts and demolishers
                game_state.attempt_spawn(DEMOLISHER, self.spawn_locs[side], count)
                game_state.attempt_spawn(SCOUT, self.spawn_locs[side], int(mp))
                
    def regular_attack(self, game_state):
        """
        regular attack logic
        """
        mp = game_state.get_resource(MP)
        if self.demolisher_required < 3:
            if mp > 8:
                game_state.attempt_spawn(SCOUT, self.spawn_locs[self.best_side], int(mp))
        elif mp >= 3*self.demolisher_required + 3:
            game_state.attempt_spawn(DEMOLISHER, self.spawn_locs[self.best_side], self.demolisher_required)
            game_state.attempt_spawn(SCOUT, self.spawn_locs[self.best_side], int(mp))
        
    def scan_and_attack(self, game_state):
        """
        scans for enemy units and attacks them
        """
        mp = game_state.get_resource(MP)
        if mp >= 3:
            game_state.attempt_spawn(DEMOLISHER, self.spawn_locs[self.best_side], 1)
            game_state.attempt_spawn(SCOUT, self.spawn_locs[self.best_side], int(mp))
        
    def run_it(self, turn_state):
        self.build_defense(turn_state)
        if not self.defend:
            self.handle_attack(turn_state)
        #insert attack logic here lmao

    def attack_v2(self, game_state:gamelib.GameState):
        self.score.append(self.ehp - game_state.enemy_health)
        #writeback
        self.ehp = game_state.enemy_health
        mp = int(game_state.get_resource(MP))
        rush_param = 1.5*(5+game_state.turn_number//10)
        #TODO: optimize this parameter
        acceptance_param = (5+game_state.turn_number//3)
        if (self.expectation[-1] - self.score[-1]) < acceptance_param:
            #we are doing well. keep going. 
            if self.demolisher_required < 3:
                #if 1 or 2 towers, we just rush wth our scouts.
                if mp > rush_param:
                    game_state.attempt_spawn(SCOUT, self.spawn_locs[self.best_side], int(mp))
                    self.expectation.append(int(mp))
        else: #we need to change something
            if mp >= 3*self.demolisher_required + 3: #spawn maximum number of demolishers to attempt to break through
                game_state.attempt_spawn(DEMOLISHER, self.spawn_locs[self.best_side], int(mp//3))
                game_state.attempt_spawn(SCOUT, self.spawn_locs[self.best_side], int(mp%3))
                self.expectation.append(int(mp//3) + int(mp%3))
        
    def scan_side(self, game_state):
        """scan if enemy has very weak side"""
        if game_state.turn_number != 0:
            for side in self.enemysides:
                attacker_count = 0
                for loc in side:
                    unit = game_state.contains_stationary_unit(loc)
                    if unit: attacker_count += 1
                if attacker_count <= 1:
                    side = not self.enemysides.index(side)
                    self.enemy_weak_side = [side, attacker_count]
                    self.best_side = side
                    gamelib.debug_write('weak side: {}, has {} turrets'.format(self.enemy_weak_side, attacker_count))
                
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
        if state['turnInfo'][1] != self.last_turn: 
            self.last_turn = state['turnInfo'][1] 
            # check if enemy used more than 10 points on attacking with demolishers and scouts
            enemy_mp_spent = 0
            scouts, demolishers = [state['p2Units'][3], state['p2Units'][4]]
            for scout in scouts:
                enemy_mp_spent += 1
            for demolisher in demolishers:
                enemy_mp_spent += 3
            if enemy_mp_spent >6:
                self.enemy_attack_thresholds.append(enemy_mp_spent)
            
            
    ### ------------------- Turn Functions ------------------- ###

    
    def build_defense(self, game_state):
        """Builds our defensive structure - with side leaning."""
        #rebuild the initial defenses
        self.check_mp(game_state)
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
        elif self.best_side == 1:
            self.select_left(game_state)
        else: # defence case, spawn interceptors
            game_state.attempt_spawn(WALL, [[3, 11], [24, 11], [9, 4], [9, 5]], 1)
            game_state.attempt_remove([[3, 11], [24, 11], [9, 4], [9, 5]])
            game_state.attempt_spawn(INTERCEPTOR, [[19, 5], [21, 7], [8, 5], [6, 7]], 1)
            #game_state.attempt_spawn(INTERCEPTOR, [[6,7],[21,7]], 1)
            
        #spawn symmetrical turret
        s = game_state.attempt_spawn(TURRET, [23, 11], 1)
        if (s==1) : 
            self.sp -= 6
        elif self.sp -6 < 0 :
            return
        #Fortify a side. 
        self.BuildL1(game_state)
        #Fortify L2s
        self.BuildL2(game_state)
        #Fortify L3s
        self.BuildL3(game_state)
        #Fortify L4s
        self.BuildL4(game_state)
        #iron man dies
        self.build_endgame(game_state)


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
        self.demolisher_required = 0

    ###-------------------- Helper Functions -------------------###

    def check_mp(self, game_state):
        gamelib.debug_write("checking mp")

        if len(self.enemy_attack_thresholds) >= 1:
            threshold = sum(self.enemy_attack_thresholds)/len(self.enemy_attack_thresholds)
            gamelib.debug_write("threshold: {}".format(threshold))
        else:
            threshold = 14
        if threshold <= game_state.get_resource(MP, 1) and game_state.get_resource(MP, 0) < 22:
            #we need to defend
            self.defend = True
        else:
            self.defend = False

    def build_endgame(self, game_state):
        walls = [[7,9],[7,8], [20,9], [20,8], [8,7],[19, 7], [9, 6],[10,6], [11,6], [12,6], [13,6], [14,6], [15,6], [16,6], [17,6], [18,6]]
        supports = [[10, 5], [11, 5], [12, 5], [13, 5], [14, 5], [15, 5], [16, 5], [17, 5], [11, 4],[12, 4], [13, 4], [14, 4],[15, 4],[16, 4],
                    [12, 3],[13, 3], [14, 3], [15, 3], [13, 2], [14, 2]]
        gunners = [[18, 7], [9,7]]
        for loca in gunners:
            game_state.attempt_spawn(TURRET, loca, 1)
            game_state.attempt_upgrade(loca)
        for loca in walls:
            game_state.attempt_upgrade(loca)
        for loca in supports:
            game_state.attempt_upgrade(loca)
        return

    

    def BuildL4(self, game_state):
        self.build_L4_supports(game_state)
        if self.fortside != 0: #we build rhs
            self.L4RHS(game_state)
            self.L4LHS(game_state)
        else: #we build lhs
            self.L4LHS(game_state)
            self.L4RHS(game_state)
        return
    
    def L4RHS(self, game_state):
        game_state.attempt_upgrade([2,11])
        game_state.attempt_upgrade([5,10])
        game_state.attempt_upgrade([6,9])
    
    def L4LHS(self, game_state):
        game_state.attempt_upgrade([25,11])
        game_state.attempt_upgrade([22,10])
        game_state.attempt_upgrade([21,9])
        walls = [[5,12], [6, 11]]
        for loca in walls:
            game_state.attempt_spawn(WALL, loca, 1)
        

    def BuildL3(self, game_state):
        if self.fortside != 0: #RHS
            self.L3RHS(game_state)
            self.L3LHS(game_state)
        else: #LHS
            self.L3LHS(game_state)
            self.L3RHS(game_state)
        self.build_L3_supports(game_state)
        return

    def L3RHS(self, game_state):
        game_state.attempt_upgrade([1,12])
        game_state.attempt_upgrade([4,11])
    
    def L3LHS(self, game_state):
        game_state.attempt_upgrade([26,12])
        game_state.attempt_upgrade([23,11])

    def BuildL2(self, game_state):
        if self.fortside != 0: #we build rhs
            self.L2RHS(game_state)
            self.L2LHS(game_state)
            self.build_L2_supports(game_state)
        else:
            self.L2LHS(game_state)
            self.L2RHS(game_state)
            self.build_L2_supports(game_state)
        return

    def L2RHS(self, game_state):
        s = game_state.attempt_spawn(TURRET, [25, 11], 1) #RHS
        if (s==1) : self.sp -= 6
        if self.sp < 6.5: return
        walls = [[21,11], [20,9], [20,8]]
        for loca in walls:
            s = game_state.attempt_spawn(WALL, loca, 1)
            if (s==1) : self.sp -= 1.5
        s= game_state.attempt_spawn(TURRET, [21, 9], 1) #RHS
        if (s==1) : self.sp -= 6

    
    def L2LHS(self, game_state):
        
        s = game_state.attempt_spawn(TURRET, [2, 11], 1) #LHS
        if (s==1) : self.sp -= 6
        if self.sp < 6.5: return
        walls = [[7,9],[7,8],[2,12]]
        for loca in walls:
            s = game_state.attempt_spawn(WALL, loca, 1)
            if (s==1) : self.sp -= 1.5
        s = game_state.attempt_spawn(TURRET, [6, 9], 1) #LHS
        if (s==1) : self.sp -= 6
    

    def BuildL1(self, game_state):
        if self.fortside != 0: #we build RHS
            self.L1RHS(game_state)
            if self.sp < 6.5: return
            s = game_state.attempt_spawn(SUPPORT, [14, 5], 1)
            if (s==1) : self.sp -= 4
            self.L1LHS(game_state)
        else:
            self.L1LHS(game_state)
            if self.sp < 6.5: return
            s = game_state.attempt_spawn(SUPPORT, [15, 5], 1)
            if (s==1) : self.sp -= 4
            self.L1RHS(game_state)
        self.build_L1_supports(game_state)
        return
        
    def L1RHS(self, game_state):
            #RHS Turret
            s = game_state.attempt_spawn(TURRET, [5, 10], 1)
            if (s==1) : self.sp -= 6
            #RHS new wall
            s = game_state.attempt_spawn(WALL, [26, 13], 1)
            if (s==1) : self.sp -= 1.5
            #RHS Wall Upgrades
            L1wallsRHS = [[22,12], [25, 12],[26, 13],[27,13],[21,10]]
            for loca in L1wallsRHS:
                s = game_state.attempt_upgrade(loca)
                if (s==1) : self.sp -= 1.5
            game_state.attempt_spawn(SUPPORT, [13, 5], 1)
    
    def L1LHS(self, game_state):
            s = game_state.attempt_spawn(TURRET, [22, 10], 1)
            if (s==1) : self.sp -= 6

            s = game_state.attempt_spawn(WALL, [1, 13], 1)
            if (s==1) : self.sp -= 1.5
            #LHS Wall Upgrades
            L1wallsLHS = [[0,13],[1,13],[2,12],[4,12]]
            for loca in L1wallsLHS:
                s = game_state.attempt_upgrade(loca)
                if (s==1) : self.sp -= 1.5

    def count_supports(self, game_state):
        return self.sup_count

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
        self.paths.append(path)
        enemy_turrets = []
        for loc in path:
            threatening_turrets = game_state.get_attackers(loc, 0)
            for threatening_turret in threatening_turrets:
                total_threat += threatening_turret.damage_i * threatening_turret.health / threatening_turret.max_health
                unit_loc = [threatening_turret.x, threatening_turret.y]
                if unit_loc not in enemy_turrets:
                    enemy_turrets.append(unit_loc)
        return total_threat, enemy_turrets

    def pick_side(self, game_state):
        """
        the algo will take care of selecting side
        """
        enemy_turret_by_path = []
        if not self.enemy_weak_side:
            sides = [0, 1]
            threats = [math.inf] * 2
            for side in sides:
                equivalent_locs = self.equivalent_locs[side]
                threat, enemy_terret_locs = self.compute_threat(game_state, equivalent_locs)
                threats[side] = threat
                enemy_turret_by_path.append(enemy_terret_locs)
            self.min_threat = min(threats)
            self.best_side = threats.index(self.min_threat)
            self.demolisher_required = len(enemy_turret_by_path[self.best_side])
            if self.defend:
                self.best_side = -1

    #L1: 115-165
    #L2: 105, 175, 114-164
    #L3: [[13, 3], [14, 3], [15, 3], [12, 3]]
    #L4: [[13, 2], [14, 2]]
    def build_L1_supports(self, game_state):
        L1 = [[13, 5], [14, 5], [15, 5], [12, 5], [16, 5], [11, 5]]
        for loca in L1:
            s = game_state.attempt_spawn(SUPPORT, loca, 1)
            if (s==1) : 
                self.sp -= 4
                self.sup_count += 1
    def build_L2_supports(self, game_state):
        L2 = [[10, 5], [17, 5],[11,4], [12, 4],[13, 4], [14, 4], [15, 4], [16, 4]]
        for loca in L2:
            s = game_state.attempt_spawn(SUPPORT, loca, 1)
            if (s==1) : 
                self.sp -= 4
                self.sup_count += 1
                
    def build_L3_supports(self, game_state):
        L3 = [[13, 3], [14, 3], [15, 3], [12, 3]]
        for loca in L3:
            s = game_state.attempt_spawn(SUPPORT, loca, 1)
            if (s==1) : 
                self.sp -= 4
                self.sup_count += 1
                
    def build_L4_supports(self, game_state):
        L4 = [[13, 2], [14, 2]]
        for loca in L4:
            s = game_state.attempt_spawn(SUPPORT, loca, 1)
            if (s==1) : 
                self.sp -= 4
                self.sup_count += 1

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
