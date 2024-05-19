'''
This is the AI base class. This module contains:

- `SystemState` class: it is a data structure capturing the one-ring vision of 
  the snake
- `AI_Base`: the base class for all AI player. It provides specification for 
  a subclass to implement own algorithm so that the subclass can plug seamlessly 
  to the environment.
'''

from abc import ABC, abstractmethod
from snake import GameOutcome

class SystemState:
    '''
    It is the System State data structure carrying the one-ring vision of 
    the snake. It also indicates the food position and carries the current
    movement of the snake.
    '''
    def __init__(self):
        ## mark the position of the food relative to the snake
        self.food_north: bool = False
        self.food_south: bool = False
        self.food_east: bool = False
        self.food_west: bool = False
        ## mark the obstacle one-ring around the snake
        self.obj_north: int = 0
        self.obj_south: int = 0
        self.obj_east: int = 0
        self.obj_west: int = 0
        self.obj_north_east: int = 0
        self.obj_north_west: int = 0
        self.obj_south_east: int = 0
        self.obj_south_west: int = 0
        ## record the current movement of the snake
        self.dir_x: int = 0
        self.dir_y: int = 0


class DecayingFloat:
    '''
    This class provides a delaying floating number. It is disguised as a 
    `float` but provides methods to trigger a decay.

    The constructor takes the following inputs parameters.

    Parameters:
    value : float
        The initial value of the decaying float number. We assume it
        is a positive value.
    factor : float, optional, default=None
        The decaying factor. If None is specified, the float number will
        not decay.
    minval : float, optional, default=None
        The minimum value of the float. If None is specified, the float
        number can reach zero which is the lowest.
    mode : str
        It can be either "exp" for exponential decaying or "linear" for
        linear decaying. An unrecognized string will cause the value 
        not to decay.
    '''
    def __init__(self, value:float, factor:float=None, minval:float=None,
                 mode:str="exp"):
        self.init = value
        self.value = value
        self.factor = factor
        self.minval = minval
        self.mode = mode

    def __float__(self) -> float:
        '''
        This method performs the type casting operation to return a float.
        '''
        return float(self.value)

    def reset(self):
        '''
        To start over the decaying function from the beginning.
        '''
        self.value = self.init

    def decay(self):
        '''
        To perform a step of decay. The decaying depends on the `factor`
        and the `mode`. If `factor` is not given or `mode` string is
        unrecognized, the method simply does nothing.
        '''
        if self.factor==None: return

        if self.mode=="exp":      self.value *= self.factor
        elif self.mode=="linear": self.value -= self.factor
        
        if self.minval==None: 
            return
        elif self.value<self.minval:
            self.value = self.minval


class AI_Base(ABC):
    '''
    This is the base class for the AI player.

    The subclass must reimplement the following two abstract methods:

    - callback_take_action(): called when the environment requests 
      your AI agent to take an action based on the current system state.
    - callback_action_outcome(): called right after the environment
      has taken the last action to report the new state and outcome.

    The subclass may reimplement the following method:

    - callback_terminating(): called when the program is just about
      to exit. The algorithm can print some final statistical info or 
      save some info before the program ends.
    '''

    def __init__(self):
        self._name = "Human Player"
        self._state: SystemState = None

    def get_name(self) -> str:
        '''Return the name of this AI algorithm.

        Returns
        -------
        str
            The name of this AI algorithm.
        '''
        return self._name

    def state_str(self, state:SystemState) -> str:
        '''Return the string representation of the system state 
        observed by this player.

        Returns
        -------
        str
            The string representation of the system state.
        '''
        return "["+(">" if state.food_east else " ") \
                  +("v" if state.food_south else " ") \
                  +("<" if state.food_west else " ") \
                  +("^" if state.food_north else " ") + "]," \
                  + "[%+d,%+d,%+d,%d]"% \
                      (state.obj_north,state.obj_south,state.obj_east,state.obj_west) \
                  + "-%s"%("U" if state.dir_y==-1 else "D" if state.dir_y==1 else \
                           "L" if state.dir_x==-1 else "R")

    def is_keyboard_allowed(self) -> bool:
        '''Return if this AI algorithm can accept keyboard input. By 
        default, it is not allowed. So user cannot interfere with 
        the decision made by this algorithm using the keyboard.

        Returns
        -------
        bool
            Whether keyboard is allowed to interfere with the decision made
            by the algorithm.
        '''
        return False

    ## callback when a request for action is needed by the environment
    @abstractmethod
    def callback_take_action(self, state:SystemState) -> (int,int):
        '''This is a callback function of the algorithm when an action
        is needed. This method is periodically called by the environment.

        This is abstract method and should be reimplemented in the
        subclass.

        Parameters
        ----------
        state : SystemState
            The current system state of the environment.

        Returns
        -------
        Tuple (int,int)
            The algorithm should return a tuple instructing the environment
            the next move of the snake. The first element in the tuple is the 
            x-direction (either -1,0,1 for left,none,right) and the second
            element is the y-direction (either -1,0,1 for up,none,right).
            In the rule, the snake cannot move diagonally, so at least one
            of the element must be a zero.
        '''
        ## if called accidentally, it simply returns the same 
        ## movement as the previous state
        return (state.dir_x,state.dir_y) 

    ## callback when the outcome for the last action is available
    @abstractmethod
    def callback_action_outcome(self, state:SystemState, outcome:GameOutcome):
        '''This is a callback function for the environment to report an outcome
        of an action made previously by the algorithm.

        This is abstract method and should be reimplemented in the
        subclass.

        Parameters
        ----------
        state : SystemState
            The current system state of the environment.
        outcome : GameOutcome
            The outcome of the action made previously.
        '''
        pass 

    def callback_terminating(self):
        '''This is a callback function which will be called when
        a termination signal is triggered in the environment. This gives
        the algorithm to perform any final processing before the game ends.
        It is useful for an algorithm to save some learned data.

        By default, it performs nothing. A subclass may overload this method
        to provide any final processing.
        '''
        pass # do nothing by default

