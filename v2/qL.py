import gymnasium as gym
from gymnasium import Env, spaces
import numpy as np
import math
import random
from collections import namedtuple, deque
from itertools import count
import json

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

class terminalSpace(Env):
    def __init__(self):
        super(terminalSpace, self).__init__()

        self._reset_self_metrics()
        
        # Define a 2-D observation space
        self.observation_space = spaces.Box(low=0, high=float('inf'), shape=(427,), dtype=np.int8)
        
        self.action_space = spaces.Box(np.array([0,0]), np.array([+30,+10]), dtype=np.int8) # 1d space (# scouts, # demolishers)

    def _refresh_state(self, action) -> json: #TODO
    
        return function(action) # -> change function() this to the func that takes in input.
        #return raw board 
        #docs -> file:///Users/peter/Desktop/terminal/json-docs.html#frame-damage
        
    def _parse_board(self, board) -> np.array:

        # parse to a 1 x 427 array, using the input board, and return that array
        
        # Grid of size 420      idx 0 - 419
            # 0 -> Nothing, 1 -> wall, 2 -> turret, 3 -> support
        # SP = 2                idx 420-421
            # val = SP value
        # MP = 2                idx 422-423
            # val = MP value
        # side = 1              idx 424
            # val = 0 -> side_0, 1 -> side_1
        # health = 2            idx 425-426 
            # our health, their health

        self.ourHealth, self.ourSP, self.ourMP = board["p1Stats"][0], board["p1Stats"][1], board["p1Stats"][2]
        self.theirHealth, self.theirSP, self.theirMP = board["p2Stats"][0], board["p2Stats"][1], board["p2Stats"][2]

        self.roundNum = board["turnInfo"][1]

        p1Arr = {}
        p2Arr = {}

        p1Wall, p1Tur, p1Sup = board["p1Units"][0], board["p1Units"][1], board["p1Units"][2]
        p2Wall, p2Tur, p2Sup = board["p2Units"][0], board["p2Units"][1], board["p2Units"][2]

        for i in p1Wall:
            p1Arr[(i[0], i[1])] = 1
        for i in p1Tur:
            p1Arr[(i[0], i[1])] = 2
        for i in p1Sup:
            p1Arr[(i[0], i[1])] = 3
        
        for i in p2Wall:
            p2Arr[(i[0], i[1])] = 1
        for i in p2Tur:
            p2Arr[(i[0], i[1])] = 2
        for i in p2Sup:
            p2Arr[(i[0], i[1])] = 3

        returnArr = []

        initStart, initEnd = 13, 15
        for y in range(0, 28):
            if y <= 12:
                for x in range(initStart, initEnd):
                    if (x, y) in p1Arr:
                        returnArr.append(p1Arr[(x, y)])
                    else:
                        returnArr.append(0)
                
                initStart -= 1
                initEnd += 1
            elif y >= 14:
                for x in range(initStart, initEnd):
                    if (x, y) in p2Arr:
                        returnArr.append(p2Arr[(x, y)])
                    else:
                        returnArr.append(0)
                
                initStart += 1
                initEnd -= 1
            else:
                for x in range(initStart, initEnd):
                    if (x, y) in p1Arr:
                        returnArr.append(p1Arr[(x, y)])
                    else:
                        returnArr.append(0)

            returnArr.extend([self.ourSP, self.theirSP, self.ourMP, self.theirMP, self.side, self.ourHealth, self.theirHealth])
        return returnArr
    
    def _calc_reward(self, board)-> float:
        breaches = board["Events"]["breach"]
        damages = board["Events"]["damage"]

        self_breached, other_breached = 0, 0
        self_damaged, other_damaged = 0, 0

        for breach in breaches:
            if breach[4] == 1:
                other_breached += 1
            else:
                self_breached += 1
        
        for damage in damages:
            if damage[4] == 2:
                other_damaged += damage[1]
            else:
                self_damaged += damage[1]
        
        return 0.5 * (other_damaged - self_damaged) + 0.5 * (other_breached - self_breached)
        # parse using the "breach" and "damage" fields
    
    def _calc_terminated(self, board)-> bool: 
        return "endStats" in board
        # prase to se if field "endStats" is in the raw board, if yes, return true
    
    def _reset_game(self) -> json: #TODO
        return None
        # do something with the two algos to revert them back to init status. Return the initial game board
    
    def _reset_self_metrics(self)-> None:
        self.ourSP, self.theirSP = 40, 40
        self.ourMP, self.theirMP = 5, 5

        self.ourHealth, self.theirHealth = 30, 30

        self.roundNum = 0

        self.side = 0

    def step(self, actions): # -> observation, reward, terminated, info
        
        #observation -> the 1 x 736 array done after action is complete
        #reward -> weighted sum of the following
            # 50% -> (points of damage to them - points of damage to us)
            # 50% -> (point they lost - points we lost)
        #terminated -> boolean, true if "endStats" in observation
        #info -> None (for now)

        newState = self._refresh_state(actions)

        parsed = self._parse_board(json.loads(newState))
        reward = self._calc_reward(json.loads(newState))
        terminated = self._calc_terminated(json.loads(newState))

        return parsed, reward, terminated, self._get_info()

    def reset(self): # -> state, info
        
        #state -> the 1 x 736 array at epoch 1 of the game
        #info -> None (for now)

        self._reset_self_metrics()
        
        return self._reset_game(), self._get_info()
    
    def _get_info(self):
        return {
            "round Num": self.roundNum,
            "ourSP": self.ourSP,
            "theirSP": self.theirSP,
            "ourMP": self.ourMP,
            "theirMP": self.theirMP,
            "ourHealth": self.ourHealth,
            "theirHealth": self.theirHealth,
        }

env = terminalSpace()

Transition = namedtuple('Transition',
                        ('state', 'action', 'next_state', 'reward'))

class ReplayMemory(object):

    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        """Save a transition"""
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)
    
class DQN(nn.Module):

    def __init__(self, n_observations, n_actions):
        super(DQN, self).__init__()
        self.layer1 = nn.Linear(n_observations, 128)
        self.layer2 = nn.Linear(128, 128)
        self.layer3 = nn.Linear(128, n_actions)

    # Called with either one element to determine next action, or a batch
    # during optimization. Returns tensor([[left0exp,right0exp]...]).
    def forward(self, x):
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))
        return self.layer3(x)

BATCH_SIZE = 99
GAMMA = 0.99
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 1000
TAU = 0.005
LR = 1e-4

# Get number of actions from gym action space
n_actions = 2
# Get the number of state observations
state, info = env.reset()
n_observations = len(state)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

policy_net = DQN(n_observations, n_actions).to(device)
target_net = DQN(n_observations, n_actions).to(device)
target_net.load_state_dict(policy_net.state_dict())

optimizer = optim.AdamW(policy_net.parameters(), lr=LR, amsgrad=True)

memory = ReplayMemory(10000)

steps_done = 0

def select_action(state):
    global steps_done
    sample = random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * \
        math.exp(-1. * steps_done / EPS_DECAY)
    steps_done += 1
    if sample > eps_threshold:
        with torch.no_grad():
            # t.max(1) will return the largest column value of each row.
            # second column on max result is index of where max element was
            # found, so we pick action with the larger expected reward.
            return policy_net(state).max(1)[1].view(1, 1)
    else:
        return torch.tensor([[env.action_space.sample()]], device=device, dtype=torch.long)
    
episode_durations = []

def optimize_model():
    if len(memory) < BATCH_SIZE:
        return
    transitions = memory.sample(BATCH_SIZE)
    # Transpose the batch (see https://stackoverflow.com/a/19343/3343043 for
    # detailed explanation). This converts batch-array of Transitions
    # to Transition of batch-arrays.
    batch = Transition(*zip(*transitions))

    # Compute a mask of non-final states and concatenate the batch elements
    # (a final state would've been the one after which simulation ended)
    non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                          batch.next_state)), device=device, dtype=torch.bool)
    non_final_next_states = torch.cat([s for s in batch.next_state
                                                if s is not None])
    state_batch = torch.cat(batch.state)
    action_batch = torch.cat(batch.action)
    reward_batch = torch.cat(batch.reward)

    # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
    # columns of actions taken. These are the actions which would've been taken
    # for each batch state according to policy_net
    state_action_values = policy_net(state_batch).gather(1, action_batch)

    # Compute V(s_{t+1}) for all next states.
    # Expected values of actions for non_final_next_states are computed based
    # on the "older" target_net; selecting their best reward with max(1)[0].
    # This is merged based on the mask, such that we'll have either the expected
    # state value or 0 in case the state was final.
    next_state_values = torch.zeros(BATCH_SIZE, device=device)
    with torch.no_grad():
        next_state_values[non_final_mask] = target_net(non_final_next_states).max(1)[0]
    # Compute the expected Q values
    expected_state_action_values = (next_state_values * GAMMA) + reward_batch

    # Compute Huber loss
    criterion = nn.SmoothL1Loss()
    loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

    # Optimize the model
    optimizer.zero_grad()
    loss.backward()
    # In-place gradient clipping
    torch.nn.utils.clip_grad_value_(policy_net.parameters(), 100)
    optimizer.step()

if torch.cuda.is_available():
    num_episodes = 600
else:
    num_episodes = 50

for i_episode in range(num_episodes):
    # Initialize the environment and get it's state
    state, info = env.reset()
    state = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
    for t in count():
        action = select_action(state)
        observation, reward, terminated, _ = env.step(action.item())
        reward = torch.tensor([reward], device=device)
        done = terminated

        if terminated:
            next_state = None
        else:
            next_state = torch.tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)

        # Store the transition in memory
        memory.push(state, action, next_state, reward)

        # Move to the next state
        state = next_state

        # Perform one step of the optimization (on the policy network)
        optimize_model()

        # Soft update of the target network's weights
        # θ′ ← τ θ + (1 −τ )θ′
        target_net_state_dict = target_net.state_dict()
        policy_net_state_dict = policy_net.state_dict()
        for key in policy_net_state_dict:
            target_net_state_dict[key] = policy_net_state_dict[key]*TAU + target_net_state_dict[key]*(1-TAU)

        target_net.load_state_dict(target_net_state_dict)

        if done:
            episode_durations.append(t + 1)
            break