'''
This module contains class implementing Reinforcement Learning 
algorithm using Deep Q-learning Network (DQN).

The following video clip explains line-by-line a generic DQN code which is 
the framework we used here:

- https://www.youtube.com/watch?v=OYhFoMySoVs

The code also follows the following tutorial:

- https://towardsdatascience.com/how-to-teach-an-ai-to-play-games-deep-reinforcement-learning-28f9b920440a
'''

from tensorflow.python.client import device_lib 
from keras.optimizers import Adam
from keras.models import Sequential
from keras.layers.core import Dense, Dropout
from keras.utils import to_categorical

## NOTE: use the following import for `Adam` and `to_categorical` instead if you encounter the following errors:
##   ImportError: cannot import name 'adam' from 'keras.optimizers'
##   ImportError: cannot import name 'to_categorical' from 'keras.optimizers'
#from tensorflow.keras.optimizers import Adam
#from tensorflow.keras.utils import to_categorical

import random
import numpy as np
import collections
import os

from ai_base import SystemState, AI_Base, DecayingFloat
from snake import GameOutcome

class AI_DQN(AI_Base):

    class Action:
        '''
        This is an inner class providing three possible actions, which 
        are FRONT, LEFT and RIGHT.
        '''
        LEFT  = 0
        FRONT = 1
        RIGHT = 2
        ALL = [LEFT, FRONT, RIGHT]
        def __init__(self, action:int=0):
            self.action = action
        def __eq__(self, action:int) -> bool:
            return self.action==action
        def __int__(self) -> int:
            return self.action
        def set_action(self, action:int):
            self.action = action
        def get_action(self):
            return self.action
        def assign_array(self, action_array):
            self.action = int(np.dot(action_array,self.ALL))
        def to_array(self) -> [int]:
            action_list = []
            for i in range(0,len(self.ALL)):
                action_list.append(1 if self.action==self.ALL[i] else 0)
            return np.asarray(action_list)
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

    class State(SystemState):
        '''
        This is an inner class for the translated system state. It 
        translates absolute direction (north/east/south/west) given by
        the environment to a relative direction (front/back/left/right), 
        relative to the movement of the snake.
        '''
        def __init__(self, other:SystemState=None):

            ## translating north/east/south/west to front/back/left/right
            ## system state now contains 7 bits
            self.obj_front = 0
            self.obj_left = 0
            self.obj_right = 0
            self.food_front = False
            self.food_back = False
            self.food_left = False
            self.food_right = False
            self.dir_x = other.dir_x if other!=None else 0
            self.dir_y = other.dir_y if other!=None else 0

            if self.dir_x==+1: # moving east
                self.obj_front = other.obj_east==-1
                self.obj_left = other.obj_north==-1
                self.obj_right = other.obj_south==-1
                self.food_front = other.food_east
                self.food_back = other.food_west
                self.food_left = other.food_north
                self.food_right = other.food_south
            elif self.dir_x==-1: # moving west
                self.obj_front = other.obj_west==-1
                self.obj_left = other.obj_south==-1
                self.obj_right = other.obj_north==-1
                self.food_front = other.food_west
                self.food_back = other.food_east
                self.food_left = other.food_south
                self.food_right = other.food_north
            elif self.dir_y==+1: # moving south
                self.obj_front = other.obj_south==-1
                self.obj_left = other.obj_east==-1
                self.obj_right = other.obj_west==-1
                self.food_front = other.food_south
                self.food_back = other.food_north
                self.food_left = other.food_east
                self.food_right = other.food_west
            elif self.dir_y==-1: # moving north
                self.obj_front = other.obj_north==-1
                self.obj_left = other.obj_west==-1
                self.obj_right = other.obj_east==-1
                self.food_front = other.food_north
                self.food_back = other.food_south
                self.food_left = other.food_west
                self.food_right = other.food_east

        def _test(self, test:bool) -> int:
            '''It translates bool to int, 1 for True, 0 otherwise.'''
            return 1 if test else 0

        def to_array(self):
            state_list = [
                self._test(self.obj_front),
                self._test(self.obj_left),
                self._test(self.obj_right),
                self._test(self.food_front),
                self._test(self.food_back),
                self._test(self.food_left),
                self._test(self.food_right),
                ## the following were used in the original tutorial
                ## but they look redundant, so removed
                #self._test(self.dir_x==+1),
                #self._test(self.dir_x==-1),
                #self._test(self.dir_y==+1),
                #self._test(self.dir_y==-1)
            ]
            return np.asarray(state_list)

        def __eq__(self, other):
            return isinstance(other, SystemState) and str(self)==str(other)
        def __hash__(self):
            return hash(str(self))
        def __str__(self):
            return str(self.to_array())

    def _build_model1(self, input:int, output:int):
        '''This model is used in the original tutorial. It is quite
        dense, and very slow in training.'''
        model = Sequential()
        model.add(Dense(50,  activation='relu', input_dim=input))
        model.add(Dense(300, activation='relu'))
        model.add(Dense(50,  activation='relu'))
        model.add(Dense(output, activation='softmax'))
        model.compile(loss='mse', optimizer=Adam(self.learning_rate))
        return model 

    def _build_model2(self, input:int, output:int):
        '''This is a lighter model mainly to get training done quicker.'''
        model = Sequential()
        model.add(Dense(30, activation='relu', input_dim=input))
        model.add(Dense(80, activation='relu'))
        model.add(Dense(30, activation='relu'))
        model.add(Dense(output, activation='softmax'))
        model.compile(loss='mse', optimizer=Adam(self.learning_rate))
        return model

    def __init__(self, training_mode:bool=True):
        '''Default constructor.'''
        super().__init__()
        self._name = "DQN " + ("" if training_mode else "(testing mode)")
        print(device_lib.list_local_devices()) # check if you have a GPU

        ## environment parameters
        self.len_action = len(self.Action().to_array())
        self.len_state = len(self.State().to_array())

        ## learning related hyperparameters
        self.learning_rate: float = 0.0005
        self.gamma: float = 0.9      # discount factor
        self.memory = collections.deque(maxlen=2500)
        self.batch_size: int = 1000  # max number for training

        ## build a neural newtork model
        self.model = self._build_model2(self.len_state, self.len_action)

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
        self.num_episodes: int = 150   # number of episodes
        self.len_episodes: int = 10000  # max number of steps in each episode

        ## environment related hyperparameters
        self.epsilon = DecayingFloat(1.0, mode="exp", factor=0.9, minval=0.1)
        #self.epsilon = DecayingFloat(0.05) # fixed value as another option
        self.training_mode: bool = training_mode # training mode (T/F)?
        if not self.training_mode:
            self.epsilon = DecayingFloat(0) # if not in training, zero exploration

        ## reward settings
        self.food_reward: int = 10   # reward for getting the snake to eat the food
        self.crash_reward: int = -10 # negative reward for being crashed

        ## system related parameters
        self.current_state = None
        self.current_action = None

        ## load weights
        self.load_weights()

    def load_weights(self):
        '''Load weights from `weights-learned.hdf5`. This is used internally.'''
        filename_weights = "weights-learned.hdf5"
        if os.path.exists(filename_weights):
            self.model.load_weights(filename_weights)
            print("- loaded '%s' into the neural network"%filename_weights)
        else:
            print("- '%s' not found, no experience is used"%filename_weights)

    def save_weights(self):
        '''Save weights to `weights.hdf5`. This is used internally.'''
        filename_weights = "weights.hdf5"
        self.model.save_weights(filename_weights)

    def state_str(self, state:SystemState) -> str:
        '''It returns the string representation of the system state 
        observed by this algorithm. This implementation uses 
        translated system state, see `AI_RLQ.State` inner class.

        Returns
        -------
        str
            The string representation of the translated system state.
        '''
        return str(self.State(state))

    def remember(self, state, action, reward, next_state, done):
        '''Store the system evolution to the memory.'''
        self.memory.append((state, action, reward, next_state, done))

    def replay(self):
        '''Replay the memory, this is where the main training happens.'''

        ## limit memory to the 'batch_size'
        if len(self.memory) > self.batch_size:
            minibatch = random.sample(self.memory, self.batch_size)
        else:
            minibatch = self.memory

        ## iterate the memory one-by-one to train the model
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = reward + self.gamma * np.amax(self.model.predict(np.array([next_state]))[0])
            target_f = self.model.predict(np.array([state]))
            target_f[0][np.argmax(action)] = target
            self.model.fit(np.array([state]), target_f, epochs=1, verbose=0)

        ## clear the trained memory to avoid duplicate training
        self.memory.clear()

    def train_short_memory(self, state, action, reward, next_state, done):
        '''Train the model with a single data point.'''
        array_shape = (1, self.len_state)
        target = reward
        if not done:
            target = reward + self.gamma * np.amax(self.model.predict(next_state.reshape(array_shape))[0])
        target_f = self.model.predict(state.reshape(array_shape))
        target_f[0][np.argmax(action)] = target
        self.model.fit(state.reshape(array_shape), target_f, epochs=1, verbose=0)
    
    def callback_take_action(self, state:SystemState) -> (int,int):
        '''Here we implement the exploration-exploitation.
        For exploration, random action is pick. For exploitatioin, 
        the best action (that is, the action that can lead to the next 
        immediate state carrying the highest Q-value based on the neural
        network) is picked.'''

        ## setup current state 's'
        s = self.State(state)
        self.current_state = s  # keep the state

        ## step 1: choose action 'a' based on the system state
        ## exploration or explotation?
        if random.uniform(0,1) < float(self.epsilon):
            ## exploration: pick a random action
            chosen_action = to_categorical(random.randint(0,self.len_action-1), 
                                           num_classes=self.len_action)
        else:
            ## exploitation: choose based on model prediction
            prediction = self.model.predict(s.to_array().reshape((1, self.len_state)))
            chosen_action = to_categorical(np.argmax(prediction[0]), 
                                           num_classes=self.len_action)

        a = self.Action()
        a.assign_array(chosen_action)
        self.current_action = a # keep the action

        ## step 2:
        ## now we need to return our action to the environment
        ## so that the environment can take action and call us back via
        ## 'callback_action_outcome()' to inform us the outcome.
        ## getxy() will translate back from FRONT/LEFT/RIGHT to (x,y) direction
        return a.to_xy(s.dir_x,s.dir_y)

    def callback_action_outcome(self, state:SystemState, outcome:GameOutcome):
        '''Here we implement the update of Q-table based on the outcome.
        This will make the algorithm learned how good its previous action
        is. The update is done using Bellman equation.'''

        ## ...continuing from 'callback_take_action()'
        ## retrieve: state, action -> next_state
        ## in DQN, state & action are presented as an array
        ## and .to_array() method will do the job
        s = self.current_state.to_array()   # was the state before our action
        a = self.current_action.to_array()  # was our action FRONT/LEFT/RIGHT
        s1 = self.State(state).to_array()   # is the state after our action
        done = False

        ## step 3: calculate the reward
        if outcome==GameOutcome.CRASHED_TO_BODY or \
           outcome==GameOutcome.CRASHED_TO_WALL:
            reward = self.crash_reward
            done = True
        elif outcome==GameOutcome.REACHED_FOOD:
            reward = self.food_reward
        else:
            reward = 0 # no reward for this time step

        ## step 4: capture the state-action in the memory
        if self.training_mode:
            ## we can train the model every time step by using
            ## train_short_memory(), but this will slow down 
            ## the running significantly
            #self.train_short_memory(s, a, reward, s1, done)
            self.remember(s, a, reward, s1, done)

        ## if end of an episode, then do the training
        if done:
            self.epsilon.decay()
            if self.training_mode:
                self.replay()
        
    def callback_terminating(self):
        '''This is a listener listening to the termination signal. When triggered,
        it saves its Q-table.'''
        self.save_weights()
