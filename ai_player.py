'''
This module contains a human player class. The class performs no decision
making. It simply allows the keyboard input so that a human user can 
play the game.
'''

from snake import GameOutcome
from ai_base import SystemState, AI_Base

class AI_Player(AI_Base):
    '''
    This class implements no policy. It simply leaves the environment
    to take the input from the keyboard to execute.
    '''

    def __init__(self):
        self._name = "Human Player"
        self._state: SystemState = None

    def is_keyboard_allowed(self) -> bool:
        '''This implementation returns True to allow keyboard input.'''
        return True 

    def callback_take_action(self, state:SystemState) -> (int,int):
        '''This implementation has no policy. It simply returns the same 
        movement as in the previous state. 
        The movement will be replaced by the keyborad input a key is pressed.'''
        return (state.dir_x,state.dir_y)

    def callback_action_outcome(self, state:SystemState, outcome:GameOutcome):
        '''There is no policy in this implementation, so this method 
        does nothing.'''
        pass # do nothing by default, ignore the outcome
