'''
This module contains class implementing Reinforcement Learning 
algorithm using SARSA. 
'''

import numpy as np
import random
import json
import os

from ai_base import SystemState, AI_Base
from snake import GameOutcome

class AI_SARSA(AI_Base):
    '''
    This is the implementation of the Reinforcement Learning algorithm.
    It uses state-action-reward-state-action (SARSA) technique.
    At the beginning, the algorithm will look for `sarsa-learned.json`
    file which contains the learned Q-table for sarsa. 
    If it is found, the algorithm will load and initialize its Q-table 
    based on the data stored in the file. If it is not found, 
    the algorithm will initialize an empty Q-table.

    When termination signal is received, the algorithm will store its
    Q-table in a JSON file named `sarsa.json`.

    The constructor takes one input parameter.

    Parameters
    ----------
    training_mode : bool, optional, default=True
        Specify if this algorithm is in training mode (or online learning
        mode). If not, then this algorithm will make decision based on 
        the established Q-table and won't perform any update to the Q-table.
    '''

    class Action:
        '''
        This is an inner class providing three possible actions, which 
        are FRONT, LEFT and RIGHT.
        '''
        LEFT  = 0
        FRONT = 1
        RIGHT = 2
        ALL = [LEFT, FRONT, RIGHT]
        def __init__(self):
            self.action = None
        def __eq__(self, action:int) -> bool:
            return self.action==action
        def __int__(self) -> int:
            return self.action
        def set_action(self, action:int):
            self.action = action
        def get_action(self):
            return self.action
        def to_xy(self, x:int, y:int) -> (int,int):
            '''It translates the relative movement to the absolute movement, and 
            returns the absolute movement as a tuple. The inputs x,y are the current 
            movement which are needed for the translation.'''
            if self.action==self.FRONT:
                pass
            elif self.action==self.LEFT: # left of (x,y) direction
                if x!=0:
                    y = -x; x = 0
                else:
                    x = y; y = 0
            elif self.action==self.RIGHT: # right of (x,y) direction
                if x!=0:
                    y = x; x = 0
                else:
                    x = -y; y = 0
            return (x,y)

    ## system state: inheriting from SystemState class
    ## but translate to relative to the movement of the snake
    class State(SystemState):
        '''
        This is an inner class for the translated system state. It 
        translates absolute direction (north/east/south/west) given by
        the environment to a relative direction (front/back/left/right), 
        relative to the movement of the snake.
        '''
        def __init__(self, other:SystemState):

            ## translating north/east/south/west to front/back/left/right
            self.obj_front = None
            self.obj_left = None
            self.obj_right = None
            self.food_front = None
            self.food_back = None
            self.food_left = None
            self.food_right = None
            self.dir_x = other.dir_x
            self.dir_y = other.dir_y

            if other.dir_x==+1: # moving east
                self.obj_front = other.obj_east
                self.obj_left = other.obj_north
                self.obj_right = other.obj_south
                self.food_front = other.food_east
                self.food_back = other.food_west
                self.food_left = other.food_north
                self.food_right = other.food_south
            elif other.dir_x==-1: # moving west
                self.obj_front = other.obj_west
                self.obj_left = other.obj_south
                self.obj_right = other.obj_north
                self.food_front = other.food_west
                self.food_back = other.food_east
                self.food_left = other.food_south
                self.food_right = other.food_north
            elif other.dir_y==+1: # moving south
                self.obj_front = other.obj_south
                self.obj_left = other.obj_east
                self.obj_right = other.obj_west
                self.food_front = other.food_south
                self.food_back = other.food_north
                self.food_left = other.food_east
                self.food_right = other.food_west
            elif other.dir_y==-1: # moving north
                self.obj_front = other.obj_north
                self.obj_left = other.obj_west
                self.obj_right = other.obj_east
                self.food_front = other.food_north
                self.food_back = other.food_south
                self.food_left = other.food_west
                self.food_right = other.food_east

        def __eq__(self, other):
            return isinstance(other, SystemState) and str(self)==str(other)
        def __hash__(self):
            return hash(str(self))
        def __str__(self):
            return "["+("<" if self.food_left else " ") \
                      +("^" if self.food_front else " ") \
                      +(">" if self.food_right else " ") \
                      +("v" if self.food_back else " ") + "]," \
                    + "[%+d,%+d,%+d]"%(self.obj_left,self.obj_front,self.obj_right)
                    ## the following state info doesn't appear to help, 
                    ## so removed
                    #+ "-%s"%("N" if self.dir_y==-1 else "S" if self.dir_y==1 else \
                    #        "W" if self.dir_x==-1 else "E")

    def __init__(self, training_mode:bool=True):
        '''Default constructor.'''
        super().__init__()
        self._name = "SARSA " \
                   + ("" if training_mode else "(testing mode)")

        ## episode related hyperparameters
        ## note: our programming control flow is environment oriented,
        ## we can't control the number of episodes and length here. They
        ## are ignored.
        ## - num_episodes: The environment sets this to infinity by default, 
        ##                 but the user can terminate at anytime by ^C or 
        ##                 choose not to continue on the popup dialog when 
        ##                 the snake crashed.
        ## - len_episodes: The environment sets this to infinity by default, 
        ##                 so the only terminating condition is a snake crash.
        self.num_episodes: int = 2000   # number of episodes
        self.len_episodes: int = 10000  # max number of steps in each episode

        ## learning related hyperparameters
        self.alpha: float = 0.2    # learning rate
        self.gamma: float = 0.9    # discount factor
        self.epsilon: float = 0.05 # exploration weight, 0=no; 1=full
        #self.epsilon = DecayingFloat(1.0, mode="exp", factor=0.9, minval=0.1)
        self.training_mode: bool = training_mode # training mode (T/F)?
        if not self.training_mode:
            self.epsilon = 0.0 # if not in training, zero exploration

        ## reward settings
        self.food_reward: int = 10   # reward for getting the snake to eat the food
        self.crash_reward: int = -10 # negative reward for being crashed

        ## Q-table: q_table[s:State][a:Action] it is a dict
        self.q_table = dict()

        ## current/next state & action
        self.current_state = None
        self.current_action = None
        #self.next_state = None # there is no need to remember next state
        self.next_action = None

        ## load Q-table
        self.load_table()


    def load_table(self):
        '''Load Q-table from `sarsa-learned.json`. This is used internally.'''
        filename_q_table = "sarsa-learned.json"
        if os.path.exists(filename_q_table):
            with open(filename_q_table, "r") as fp:
                self.q_table = json.load(fp)
            if len(self.q_table)!=0:
                print("- loaded '%s' which contains %d states"
                            %(filename_q_table,len(self.q_table)))
        else:
            print("- '%s' not found, no experience is used"%filename_q_table)

    def save_table(self):
        '''Save Q-table to `sarsa.json`. This is used internally.'''
        class NpEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                else:
                    return super(NpEncoder, self).default(obj)

        ## write Q-Table to the json file
        ## this way, we don't lose the training data
        with open("sarsa.json", "w") as fp:
            json.dump(self.q_table, fp, cls=NpEncoder, indent=4)

    def state_str(self, state:SystemState) -> str:
        '''It returns the string representation of the system state 
        observed by this algorithm. This implementation uses 
        translated system state, see `AI_SARSA.State` inner class.

        Returns
        -------
        str
            The string representation of the translated system state.
        '''
        return str(self.State(state))

    ## helper function, easy access to the Q-table
    def q(self, state):
        '''It provides easy access to Q-table, i.e. use `q(s)[a]` to access
        the Q-value of state `s` and action `a`.

        Parameters
        ----------
        state : AI_RLQ.State
            The translated system state instance.
        '''
        s = str(state) # we use str to index Q-table, easier to debug
        if s not in self.q_table:
            ## create a row for this new state in Q-table
            self.q_table[s] = np.zeros(len(self.Action.ALL))
        return self.q_table[s]

    def _decide_action(self, state:SystemState):
        '''Given a state, the ML agent decides what action to
        take. This depends on whether to do exploration or 
        exploitation. 
        It returns the decided `Action` object.'''

        s = self.State(state)
        a = self.Action()
        possible_actions = []

        if random.uniform(0, 1) < self.epsilon:
            ## exploration: include all actions
            possible_actions = self.Action.ALL.copy()
        else:
            ## exploitation: limit to the choice based on optimal policy
            ## may have multiple same max value
            ## ie. pi_star(s) = argmax_a(Q_star(s,a))
            max_value = np.max(self.q(s)) # find the max value first
            for i in self.Action.ALL:
                if self.q(s)[i]==max_value:
                    possible_actions.append(i) # add all carrying max value

        a.set_action(random.choice(possible_actions))
        return a

    def callback_take_action(self, state:SystemState) -> (int,int):
        '''Here we implement SARSA. SARSA needs to decide the next
        action during the update of Q-table. The next action is
        stored in `self.next_action`. Here, we only need to return
        the already decided next action.'''

        ## first time without `next_action`?
        if self.next_action is None:
            self.next_action = self._decide_action(state)

        ## keep current (s,a)
        s = self.State(state)
        self.current_state = s  # keep the state
        a = self.next_action
        self.current_action = a # take the next_action & execute it
        return a.to_xy(s.dir_x,s.dir_y)

    def callback_action_outcome(self, state:SystemState, outcome:GameOutcome):
        '''Here we implement the update of Q-table based on the outcome.
        This will make the algorithm learned how good its previous action
        is. The update is done using SARSA.'''

        ## ...continuing from 'callback_take_action()'
        ## retrieve: state, action -> next_state
        s  = self.current_state      # was the state before our action
        a  = self.current_action     # was our action FRONT/LEFT/RIGHT
        s1 = self.State(state)       # is the state after our action

        ## decide next action
        a1 = self._decide_action(state) # is the next action
        self.next_action = a1

        ## step 3: calculate the reward
        if outcome==GameOutcome.CRASHED_TO_BODY or \
           outcome==GameOutcome.CRASHED_TO_WALL:
            reward = self.crash_reward
        elif outcome==GameOutcome.REACHED_FOOD:
            reward = self.food_reward
        else:
            reward = 0 # no reward for this time step

        ## step 4: update Q table using SARSA
        ## Q_next(s,a) = Q(s,a) \
        ##               + alpha * (reward + gamma*Q(s_next,a_next)) - Q(s,a))
        ##             = (1-alpha) * Q(s,a)
        ##               + alpha  * (reward + gamma*Q(s_next,a_next))
        ## update Q-Table only if we're in the training mode
        if self.training_mode:
            a = int(a)   # 'a' needs to be an integer now to index the Q-table
            a1 = int(a1) # 'a1' needs to be an integer now to index the Q-table
            self.q(s)[a] = self.q(s)[a] \
                 + self.alpha * (reward + self.gamma*self.q(s1)[a1] - self.q(s)[a])
        
    def callback_terminating(self):
        '''This is a listener listening to the termination signal. When triggered,
        it saves its Q-table.'''
        self.save_table()
