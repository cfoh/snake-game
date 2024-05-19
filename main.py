'''
This is the main program. The main() function is just a launcher.
It sets parameters and create & run the application.

`MainApp` class is the application that runs the main loop and dispatches
events. 
'''

import os
import sys
import pygame
from pygame import Surface
import argparse
from argparse import Namespace, ArgumentParser
import random
import tkinter as tk
from tkinter import messagebox as msgbox

## own modules
from snake import GameWorld, GameOutcome, SnakeVision
from ai_base import SystemState, AI_Base
from ai_player import AI_Player
from ai_rulebased import AI_RuleBased
from ai_rlq import AI_RLQ
from ai_sarsa import AI_SARSA
from ai_dqn import AI_DQN

class MainApp:
    '''
    This is the main application. It creates an environment for AI to
    make decision and learn the outcome. The environment runs a loop 
    to perform the following tasks:

    - present to the algorithm with the current system state and 
      ask to make a move (see `self.make_a_move()`)
    - check the keyboard input and process it
    - execute the move and update the screen
    - present to the algorithm with the outcome and the new system 
      state (see `self.report_outcome_to_AI()`)
    - repeat the process again
    
    It has several listeners:

    - on_init(): called during the initialization process.
    - on_event(): called when a user or timer event occurs. It also dispatches 
      the raw event to other relevant listeners.
    - on_key_event(): called when a key is pressed or released.
    - on_paint(): called when the frame requires an update on the screen.
    - on_exit(): called when a user requested to exit the application.
    - tk_callback_quit(): called when `tk` receives a close window from the user.
    '''

    def __init__(self, args:Namespace, algo:AI_Base):

        ## AI element
        self._algo = algo

        ## game elements
        self._speed: int = args.speed
        self._high_score: int = 0
        self._round: int = 0
        self._pause_mode: bool = not args.nopause # allowing pause?
        self._gui_mode: bool = not args.nodisplay # allowing GUI?
        self._snake_game = GameWorld(15,20)  # setup the width & height of the world
        self._surface: Surface # hold a surface for drawing

        ## fps elements
        self._game_frame: int = 0
        self._game_fps: float = 0
        self._game_ticks: float = 0
        self._game_default_fps: int = 120

        ## tk elements
        self._tk_root = tk.Tk()
        self._text: tk.Text

        ## main loop control elements
        self._running: bool = True
        self._user_quitting: bool = False
        self._clock = pygame.time.Clock()
 
    def tk_callback_quit(self):
        self._user_quitting = True

    def on_init(self):
        ## initialize pygame engine
        pygame.init()
        pygame.display.set_caption("Let's play Snake!")
        pygame.time.set_timer(pygame.USEREVENT, self._speed, True)

        ## GUI display option
        if self._gui_mode:
            ## create a surface (ie canvas) for the game to do drawing
            app_scr_width, app_scr_height = self._snake_game.get_screen_size()
            self._surface = pygame.display.set_mode((app_scr_width,app_scr_height))

            ## hook a text widget to the root
            self._text = tk.Text(self._tk_root, height=18, width=50)
            self._text.configure(font=('Consolas', 16))
            self._text.configure(state='normal')
            self._text.pack()

            ## hook the root to a tk frame for debugging
            self._tk_root.protocol("WM_DELETE_WINDOW", self.tk_callback_quit)
            self._tk_root.title("Debugging Window")
            tk.Frame(self._tk_root,width=400,height=100).pack()
        else:
            print("AI engine = "+self._algo.get_name())

        ## always start with pausing in GUI mode
        if self._gui_mode:
            self._snake_game.set_pause(True)
        else:
            self._snake_game.set_pause(False)

    def on_event(self, event):
        if event.type==pygame.QUIT:
            self.tk_callback_quit() # trigger tk QUIT event
        elif event.type == pygame.USEREVENT:
            # timer event, process AI movement...
            if not self._snake_game.get_pause_status(): # do only if not pause
                self.make_a_move() # ask AI to make a move
                outcome = self._snake_game.snake_take_step()
                self.on_paint()    # show the outcome on the screen
                self.report_outcome_to_AI(outcome)
                if outcome==GameOutcome.CRASHED_TO_WALL or \
                   outcome==GameOutcome.CRASHED_TO_BODY:
                    score = self._snake_game.get_score()
                    if score > self._high_score: self._high_score = score
                    self._round += 1
                    print("round, %d, score, %d"%(self._round,score))
                    if self._pause_mode and self._gui_mode:
                        if msgbox.askyesno( \
                            "Your Snake Crashed", \
                            "Game Over\nDo you want to play again?"):
                            self._snake_game.restart()
                            self._snake_game.set_pause(True)
                        else:
                            self._running = False
                    else:
                        self._snake_game.restart() # always continue for no display
                        self._snake_game.set_pause(False) # and don't pause
                elif outcome==GameOutcome.REACHED_FOOD:
                    pass # Food eaten, we can do something here
                         # but for now, we do nothing
            # keep the timer running
            pygame.time.set_timer(pygame.USEREVENT, self._speed, True)
        elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            self.on_key_event(event)

    def on_key_event(self, event):
        if not self._gui_mode: return # skip input event if no GUI

        # process pause key
        if event.type == pygame.KEYDOWN and event.key==pygame.K_SPACE:
            self._snake_game.toggle_pause()

        # process other keys if keyboard is allowed
        if self._algo.is_keyboard_allowed():
            if event.type == pygame.KEYDOWN:
                dir_x,dir_y = self._snake_game.get_direction()
                if event.key==pygame.K_UP and dir_y!=1:
                    self._snake_game.snake_change_dir(0,-1)
                elif event.key==pygame.K_DOWN and dir_y!=-1:
                    self._snake_game.snake_change_dir(0,1)
                elif event.key==pygame.K_LEFT and dir_x!=1:
                    self._snake_game.snake_change_dir(-1,0)
                elif event.key==pygame.K_RIGHT and dir_x!=-1:
                    self._snake_game.snake_change_dir(1,0)
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_UP, pygame.K_DOWN, \
                                pygame.K_LEFT, pygame.K_RIGHT]:
                    pass # do nothing for key_up

    def _get_state(self) -> SystemState:
        ## fill the input system state accordingly
        state = SystemState()
        snake_x, snake_y = self._snake_game.get_snake_loc()
        food_x, food_y = self._snake_game.get_food_loc()

        ## 1. moving direction
        state.dir_x, state.dir_y = self._snake_game.get_direction()

        ## 2. food direction
        if food_x > snake_x:   state.food_east = True
        elif food_x < snake_x: state.food_west = True
        if food_y > snake_y:   state.food_south = True
        elif food_y < snake_y: state.food_north = True

        ## 3. vision around the snake (one ring vision)
        def macro_set(x,y): ## macro-like function
            obj = self._snake_game.get_object_at(x,y)
            return 0 if obj==SnakeVision.SPACE else \
                  +1 if obj==SnakeVision.FOOD  else \
                  -1
        state.obj_north = macro_set(snake_x,snake_y-1)
        state.obj_south = macro_set(snake_x,snake_y+1)
        state.obj_east = macro_set(snake_x+1,snake_y)
        state.obj_west = macro_set(snake_x-1,snake_y)
        state.obj_north_east = macro_set(snake_x+1,snake_y-1)
        state.obj_north_west = macro_set(snake_x-1,snake_y-1)
        state.obj_south_east = macro_set(snake_x+1,snake_y+1)
        state.obj_south_west = macro_set(snake_x-1,snake_y+1)

        return state

    def make_a_move(self):
        ## run the algo based on the system state
        x,y = self._algo.callback_take_action(self._get_state())
        self._snake_game.snake_change_dir(x,y)

    def report_outcome_to_AI(self, outcome:GameOutcome):
        self._algo.callback_action_outcome(self._get_state(),outcome)
        
    def on_paint(self):
        if not self._gui_mode: return # skip if display is OFF

        ## get the game to do the drawing first
        self._snake_game.do_paint(self._surface, self._high_score)
        pygame.display.update()

        ## calculate fps
        self._clock.tick(self._game_default_fps) # fps setting
        self._game_frame += 1
        if self._game_frame%10 == 0:
            t = pygame.time.get_ticks()
            self._game_fps = (float(10)*1000.0)/(t-self._game_ticks)
            self._game_ticks = t
            self._game_frame = 0

        ## print debugging info
        self._text.delete('1.0', tk.END)
        self._text.insert('1.0', "\n"*15)
        self._text.insert('1.0', "%5.1f FPS"%self._game_fps)
        self._text.insert('3.0', "        ")
        self._text.insert('4.0', "   +---+")
        self._text.insert('5.0', "   |   |")
        self._text.insert('6.0', "   |   |   ")
        self._text.insert('7.0', "   |   |")
        self._text.insert('8.0', "   +---+")
        self._text.insert('9.0', "        ")
        self._text.insert('12.0',"state="+self._algo.state_str(self._get_state()))
        self._text.insert('14.0',self._algo.get_name())

        ## get & print snake's vision
        objlist = { SnakeVision.WALL : "W", \
                    SnakeVision.FOOD : "o", \
                    SnakeVision.BODY : "S", \
                    SnakeVision.HEAD : "H", \
                    SnakeVision.SPACE : " ", \
                    SnakeVision.OUTOFSCOPE : " " }
        snake_x, snake_y = self._snake_game.get_snake_loc()
        for x in range(-1,2):
            for y in range(-1,2):
                obj = objlist[self._snake_game.get_object_at(snake_x+x, snake_y+y)]
                self._text.delete(str(y+6)+"."+str(x+5))
                self._text.insert(str(y+6)+"."+str(x+5), obj)

        ## get & print where the food is
        food_x, food_y = self._snake_game.get_food_loc()
        if food_x > snake_x:
            self._text.delete("6.10")
            self._text.insert("6.10", ">")
        elif food_x < snake_x:
            self._text.delete("6.2")
            self._text.insert("6.2", "<")
        if food_y > snake_y:
            self._text.delete("9.5")
            self._text.insert("9.5", "v")
        elif food_y < snake_y:
            self._text.delete("3.5")
            self._text.insert("3.5", "^")

        ## print snake's moving direction
        x,y = self._snake_game.get_direction()
        if x==+1: self._text.insert("10.0", "Moving RIGHT")
        elif x==-1: self._text.insert("10.0", "Moving LEFT")
        elif y==+1: self._text.insert("10.0", "Moving DOWN")
        elif y==-1: self._text.insert("10.0", "Moving UP")

        ## update tk widget
        self._tk_root.update()

    def on_exit(self):
        pygame.quit()
 
    def run(self):
        self.on_init()

        ## this is the main loop
        while self._running:
            try:
                for event in pygame.event.get():
                    self.on_event(event) # process timer/key/mouse events if any
                self.on_paint()          # paint the game surface
                if self._user_quitting:  # process quitting request (in GUI mode)
                    if self._gui_mode \
                        and msgbox.askyesno("Quit", \
                            "Do you want to exit the application?"):
                        self._running = False
                    else: 
                        self._user_quitting = False
            except KeyboardInterrupt: # process [^C], mainly for non-GUI mode
                print(" exiting...")
                self._running = False
        self._algo.callback_terminating()
        self.on_exit()

'''
main()
'''
if __name__ == "__main__" :

    ## command line parameters
    parser: ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("--nodisplay", help="Run in no GUI mode", action="store_true")
    parser.add_argument("--nopause", help="Run without pausing", action="store_true")
    parser.add_argument("--speed", type=int, default=300)
    args: Namespace = parser.parse_args()

    ## welcome info
    print("Let's play Snake. Press [^C] to quit")

    ## do some hardcoding for debugging 
    #args.nodisplay = True  # <-- hardcoding no GUI mode
    args.nopause = True  # <-- hardcoding no pausing mode
    args.speed = 40     # <-- hardcoding the speed

    ## AI selector, pick one:
    #algo = AI_Player()      # do nothing, let human player control
    #algo = AI_RuleBased()   # rule-based algorithm
    #algo = AI_RLQ()         # Q-learning - training mode
    #algo = AI_RLQ(False)    # Q-learning - testing mode, no exploration
    algo = AI_SARSA()       # SARSA - training mode
    #algo = AI_SARSA(False)  # SARSA - testing mode, no exploration
    #algo = AI_DQN()         # DQN - training mode
    #algo = AI_DQN(False)    # DQN - testing mode, no exploration

    ## for human/algo setting adjustment
    if "Human" in algo.get_name():
        if args.nodisplay:
            print("- this is Human Player version, 'nodisplay' is ignored")
            args.nodisplay = False
        if args.speed<300:
            print("- this is Human Player version, slowing speed to 300 ms")
            args.speed = 300
        if args.nopause:
            print("- this is Human Player version, 'nopause' is ignored")
            args.nopause = False
    else:
        if args.nodisplay:
            print("- 'nodisplay' is set, setting 'speed' to 1 ms (i.e. min delay)")
            args.speed = 1
        if args.nodisplay and not args.nopause:
            print("- 'nodisplay' is set, 'nopause' to automatically enforced")
            args.nopause = True
    print("- game speed set to %d ms"%args.speed)
    print("- game will%spause between rounds"%(" not "if args.nopause else " "))
    print("")

    ## create and run the app
    main_app = MainApp(args, algo)
    main_app.run()
