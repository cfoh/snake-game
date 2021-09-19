'''
This module provides the snake game environment. It contains the following
classes:

- `GameWorld`: the main class, a.k.a the World.
- `GameOutcome`: the data structure of the game outcome.
- _GamePlayer: this is the snake in the game (private class).
- _GameFood: this is the food in the game (private class).
'''

import pygame
import random
import enum
from pygame import Surface
from vecint2 import VecInt2

class GameOutcome(enum.Enum):
    '''This class contains the constants describing the game outcome.'''
    RUNNING = 1
    PAUSE   = 2
    CRASHED_TO_WALL = 3
    CRASHED_TO_BODY = 4
    REACHED_FOOD    = 5

class SnakeVision(enum.Enum):
    '''This class contains the constants describing what the snake can see.'''
    WALL = 1
    FOOD = 2
    SPACE = 3
    BODY  = 4
    HEAD  = 5
    OUTOFSCOPE = 6

class GameWorld:
    '''
    This class describe the world of the snake game. The constructor
    takes two inputs.

    Parameters
    ----------
    width : int
        The width of the world.
    height : int
        The height of the world.
    '''
    ## static global settings
    ## images for wall, snake & food are a square block, 
    ## _block_size captures the size in pixels
    _block_size: int = 20 
    _margin_size: int = _block_size

    _img_wall:Surface = pygame.image.load("img/wall.png")
    _img_snake:Surface = pygame.image.load("img/snake.png")
    _img_head:Surface = pygame.image.load("img/head.png")
    _img_food:Surface = pygame.image.load("img/food.png")

    def __init__(self, width:int, height:int):
        ## setup the size
        self._size = VecInt2(width+2,height+2) # _size includes walls
        self._screen_size = VecInt2(0,0)
        self._screen_size.x = (self._size.x)*self._block_size + 2*self._margin_size
        self._screen_size.y = (self._size.y)*self._block_size + 2*self._margin_size + 60

        ## setup game related properties
        self._score: int = 0
        self._pause: bool = True

        ## setup other objects
        self._snake = _GameSnake(self._size)
        self._food = _GameFood(self._size)

    def restart(self):
        '''It resets the internal variables preparing for a new round of game.'''
        self._score = 0
        self._pause = True
        self._snake.restart()
        self._food.restart()

        self.debug_place_food_precisely() ##debugging


    def debug_place_food_precisely(self):
        return
        #####debugging:place food near the snake
        self._snake.restart()
        self._snake.do_move() # move the snake up a few times
        self._snake.do_move() # move the snake up a few times
        self._snake.do_move() # move the snake up a few times
        self._snake.do_move() # move the snake up a few times
        self._snake.do_move() # move the snake up a few times
        self._snake.do_move() # move the snake up a few times
        self._snake.do_move() # move the snake up a few times
        snake_loc = self._snake.get_head_loc()
        self._food.set_loc(snake_loc.x+2,snake_loc.y+2)
        #####end-debugging

    def get_object_at(self, x:int, y:int) -> SnakeVision:
        '''It return what object is at game location (x,y). Note that
        game location (0,0) is the top left corner of the wall, and 
        (self._size-1,self._size-1) is the bottom right corner of the wall.'''
        loc = VecInt2(x,y)
        if x<0 or x>self._size.x-1:
            return SnakeVision.OUTOFSCOPE
        elif y<0 or y>self._size.y-1:
            return SnakeVision.OUTOFSCOPE
        elif x==0 or x==self._size.x-1:
            return SnakeVision.WALL
        elif y==0 or y==self._size.y-1:
            return SnakeVision.WALL
        elif self._snake.is_on_body(loc):
            return SnakeVision.BODY
        elif self._snake.is_on_head(loc):
            return SnakeVision.HEAD
        elif self._food.get_loc().is_same_loc_as(loc):
            return SnakeVision.FOOD
        else:
            return SnakeVision.SPACE

    def get_screen_size(self) -> (int,int):
        '''It returns the screen size in pixels.'''
        return (self._screen_size.x,self._screen_size.y)

    def get_direction(self) -> (int,int):
        '''It returns the current moving direction of the snake.'''
        movement = self._snake.get_direction()
        return (movement.x,movement.y)

    def get_score(self) -> int:
        '''It returns the current score of the game.'''
        return self._score

    def get_snake_loc(self) -> (int,int):
        '''It returns the current location of the snake's head.'''
        x = self._snake.get_head_loc().x
        y = self._snake.get_head_loc().y
        return (x,y)

    def get_food_loc(self) -> (int,int):
        '''It returns the current food location.'''
        x = self._food.get_loc().x
        y = self._food.get_loc().y
        return (x,y)

    def _get_pixel_loc(self, pt:VecInt2) -> VecInt2:
        '''It returns the pixel location given game location `pt`.'''
        pixel_loc = VecInt2()
        pixel_loc.x = self._margin_size + pt.x*self._block_size
        pixel_loc.y = self._margin_size + pt.y*self._block_size
        return pixel_loc

    def do_paint(self, surface:Surface, highscore:int):
        '''It draws the game on the given surface.'''
        ## paint a white background and put the walls
        x = self._margin_size
        y = self._margin_size
        left: int = self._margin_size
        right: int = self._margin_size + (self._size.x-1) * self._block_size
        surface.fill((255, 255, 255))
        ## 1. top walls
        for _ in range(self._size.x):
            surface.blit(self._img_wall, (x,y))
            x += self._block_size
        ## 2. left & right walls
        y += self._block_size
        for _ in range(self._size.y-2):
            surface.blit(self._img_wall, (left,y)) # left wall
            surface.blit(self._img_wall, (right,y)) # right wall
            y += self._block_size
        ## 3. bottom walls
        x = self._margin_size
        for _ in range(self._size.x):
            surface.blit(self._img_wall, (x,y)) 
            x += self._block_size

        ## write score & high_score
        score: str = "SCORE: "+str(self._score).ljust(5)
        score += "HIGHEST SCORE: "+str(highscore)
        img_text:Surface = pygame.font.SysFont('Consolas',18,True).render(score,True,(0,0,0))
        x = int((self._screen_size.x - img_text.get_width())/2)
        y += 2*self._block_size
        surface.blit(img_text, (x,y))

        ## draw the food
        pt = self._food.get_loc()
        surface.blit(self._img_food, self._get_pixel_loc(pt).xy())

        ## draw the snake
        for i in range(len(self._snake.get_body_loc())):
            pt_list = self._snake.get_body_loc()
            if i==0:
                surface.blit(self._img_head, self._get_pixel_loc(pt_list[i]).xy())
            else:
                surface.blit(self._img_snake, self._get_pixel_loc(pt_list[i]).xy())

        ## show pause if needed
        if self._pause:
            img_text = pygame.font.SysFont('Consolas',36,True) \
                                  .render('PAUSE',True,(128,0,0))
            x = int((self._screen_size.x - img_text.get_width())/2)
            y = int((self._screen_size.y - img_text.get_height())/2)
            surface.blit(img_text, (x,y))

    def snake_change_dir(self, x:int, y:int):
        '''Use this method to change the snake moving direction.'''
        if self._pause: return
        self._snake.do_change_dir(x,y)

    def snake_take_step(self) -> GameOutcome:
        '''Use this method to trigger the snake to move one step.'''
        ## do nothing during PAUSE
        if self._pause: 
            return GameOutcome.PAUSE

        ## move the snake
        self._snake.do_move()

        ## check the outcome
        snake_head: VecInt2 = self._snake.get_head_loc()
        if snake_head.x==0 or snake_head.x==self._size.x-1 \
           or snake_head.y==0 or snake_head.y==self._size.y-1:
            ## if crashed, do the following
            return GameOutcome.CRASHED_TO_WALL
        elif self._snake.is_on_body(snake_head):
            ## if crashed, do the following
            return GameOutcome.CRASHED_TO_BODY
        elif snake_head.is_same_loc_as(self._food.get_loc()):
            ## if food eaten, do the following
            self._score += 1
            #####if self._snake.get_body_len()==1: ##debugging:limit grow
            self._snake.do_grow() ##debugging:mask for no grow
            while True:
                new_food_loc = self._food.do_place_random()
                if self._snake.is_on_body(new_food_loc):
                    continue # food on the body, try again
                elif self._snake.is_on_head(new_food_loc):
                    continue # food on the head, try again
                elif self._snake.get_head_loc().distance_to(new_food_loc)<2.0:
                    continue # food too close to the head, try again
                else: break # otherwise, done & break
            self.debug_place_food_precisely() ##debugging
            return GameOutcome.REACHED_FOOD
        return GameOutcome.RUNNING

    def toggle_pause(self) -> bool:
        '''Use this method to toggle the pause status.'''
        self._pause = not self._pause
        return self._pause

    ## method to set pause status
    def set_pause(self, pause:bool):
        '''Use this method to set pause status.'''
        self._pause = pause

    ## return the pause status
    def get_pause_status(self) -> bool:
        '''Use this method get the pause status.'''
        return self._pause

class _GameSnake:
    '''
    This is an internal class describing the behaviour of the snake in the 
    game world.
    '''

    def __init__(self, size:VecInt2):
        self._size: VecInt2 = size
        self._body: [VecInt2] = []
        self._movement: VecInt2 = VecInt2(0,0)
        self.restart() # initialization

    def restart(self):
        ## initialize the snake near the bottom center
        self._body.clear()
        x = int(self._size.x/2)
        y = self._size.y - 3
        self._body.append(VecInt2(x,y))

        ## initialize the movement to upward
        self._movement.set_xy(0,-1)

    def is_on_body(self, loc:VecInt2) -> bool:
        '''Use it to check if `loc` is on the snake body.'''
        for i in range(len(self._body)):
            if i==0: continue # skip the head
            if loc.is_same_loc_as(self._body[i]):
                return True
        return False

    def is_on_head(self, loc:VecInt2) -> bool:
        '''Use it to check if `loc` is on the snake head.'''
        return loc.is_same_loc_as(self._body[0])

    def get_body_loc(self) -> [VecInt2]:
        '''Use it to get the snake body's location info in a list of VecInt2.'''
        return self._body

    def get_body_len(self) -> int:
        '''Use it to get the length of the snake body.'''
        return len(self._body)

    def get_head_loc(self) -> VecInt2:
        '''Use it to get the head location of the snake.'''
        return self._body[0]

    def get_direction(self) -> VecInt2:
        '''It returns the moving direction of the snake.'''
        return self._movement

    def do_move(self):
        '''Call this method to trigger the snake to move one step.'''
        for i in range(len(self._body)-1,0,-1):
            self._body[i].set_to(self._body[i-1])
        self._body[0].move(self._movement)

    def do_change_dir(self, x:int, y:int):
        '''Call this method to change the snake's moving direction.'''
        self._movement.set_xy(x,y)

    def do_grow(self):
        '''Call this method to grow the snake by one block size. In the game,
        the snake grows after eating the food.'''
        x = self._body[-1].x
        y = self._body[-1].y
        self._body.append(VecInt2(x,y)) # append the body by 1 block


class _GameFood:
    '''
    This is an internal class describing the behaviour of the food.
    '''

    def __init__(self, size:VecInt2):
        self._size:VecInt2 = size
        self._location = VecInt2(0,0)
        self.restart()

    def restart(self):
        # place the food on the top half initially
        x = random.randint(1, self._size.x-2)
        y = random.randint(1, int((self._size.y-2)/2))
        self._location.set_xy(x,y)

    def do_place_random(self) -> VecInt2:
        '''Use this method to place the food at a random location.'''
        x = random.randint(1, self._size.x-2)
        y = random.randint(1, self._size.y-2)
        self._location.set_xy(x,y)
        return self._location

    def get_loc(self) -> VecInt2:
        '''It returns the location of the food.'''
        return self._location

    def set_loc(self, x:int, y:int):
        '''Use this method to set the location of the food.'''
        self._location.set_xy(x,y)

