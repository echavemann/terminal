from gymnasium import Env, spaces
import numpy as np

class terminalSpace(Env):
    def __init__(self):
        super(terminalSpace, self).__init__()
        
        # Define a 2-D observation space
        self.observation_shape = (600, 800, 3)
        self.observation_space = spaces.Box(low = np.zeros(self.observation_shape), 
                                            high = np.ones(self.observation_shape),
                                            dtype = np.float16)
        
        self.action_space = spaces.Box(np.array([0,0]), np.array([+30,+10])) # 1d space (# scouts, # demolishers)

