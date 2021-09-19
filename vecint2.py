'''
This module provides a vector object containing 2 integers with methods to 
perform manipulations.
'''

# to cope with forward declaration for type annotation
# the following works for Python 3.7+
# expect to become a default in Python 3.10
from __future__ import annotations
import math

class VecInt2:
    '''
    This class provides a vector object containing two integers.
    '''

    def __init__(self, x:int=0, y:int=0):
        self.x: int = x
        self.y: int = y

    def __add__(self, other):
        '''This is an Add operation.'''
        return VecInt2(self.x+other.x, self.y+other.y)

    def __sub__(self, other):
        '''This is a Subtraction operation.'''
        return VecInt2(self.x-other.x, self.y-other.y)

    def set_xy(self, x:int, y:int):
        '''Use this method to directly set its (x,y).'''
        self.x = x
        self.y = y

    def set_to(self, other:VecInt2):
        '''Use this method to set its (x,y) to `other`.'''
        self.x = other.x
        self.y = other.y

    def move(self, other:VecInt2):
        '''Use this method to linearly move it by `other`.'''
        self.x += other.x
        self.y += other.y

    def distance_to(self, other:VecInt2) -> float:
        '''It measures the distance between this object and `other`.'''
        p2: VecInt2 = self - other
        return float(math.sqrt(p2.x**2 + p2.y**2))

    def xy(self):
        '''It returns a tuple (x,y) describing this object.'''
        return (self.x,self.y)

    def is_same_loc_as(self, other:VecInt2) -> bool:
        '''It checks if the object has the same (x,y) as `other`.'''
        if self.x==other.x and self.y==other.y:
            return True
        return False
