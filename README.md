# Deep Reinforcement Learning
## Project: Train AI to play Snake
Table of Contents:
- Introduction
- Installation of Pyhton and important packages
- Running the program
- Managing the trained data
- Can AI play a perfect game?

## Introduction
This is a training material for my undergraduate students who are relatively new to AI, but interested to learn reinforcement learning (RL). This material is prepared based on another online tutorial:
https://towardsdatascience.com/how-to-teach-an-ai-to-play-games-deep-reinforcement-learning-28f9b920440a

The goal of this project is to develop an AI Bot to learn and play the popular game Snake from scratch. The implementation includes playing by human player, using a rule-based policy, Q-learn, and finally Deep Q-Network (DQN) algorithms. For Q-learning and DQN, no strategy is explicitly taught, the AI Bot has to try exploring all options to learn what to do to get a good reward.

The snake will get a reward after eating the food. It needs to make a series of right movements to approach and eventually land on the food. Since most movements do not get a reward, only the final movement that moves the snake onto the food will, the snake must learn how all previous movements contribute to the objective of reaching the food. `Q-learning` is specifically designed to deal with **chaining** a series of right actions that can eventually arrive to the objective and get a big reward. The idea was introduced in 1989 by Chris Watkins in his PhD thesis "Learning from Delayed Rewards":
http://www.cs.rhul.ac.uk/~chrisw/thesis.html

## Install
This project requires Python 3.8 with the pygame library installed, as well as Keras with Tensorflow backend.
```bash
git clone https://put.the.website.here/snake.git
```

## Run
To run the game, executes in the folder:
```bash
python main.py
```

The program is set to human player by default. Type the following to see available options:
```bash
python main.py --help
```

To change to a Bot, modify main.py by uncommenting the corresponding algorithm to run:
```python
    ## AI selector, pick one:
    algo = AI_Player()    # do nothing, let human player control
    #algo = AI_RuleBased() # rule-based algorithm
    #algo = AI_RLQ()       # Q-learning - training mode
    #algo = AI_RLQ(False)  # Q-learning - testing mode, no exploration
    #algo = AI_DQN()       # DQN - training mode
    #algo = AI_DQN(False)  # DQN - testing mode, no exploration
```

## Trained Data (for Q-Learning)
The trained data (i.e. Q-table) will be stored in the following file. If one already exists, it will be overwritten.
```
q-table.json
```



When launching, the program will read the following Q-table. To use the previously trained data, simply rename it to the following filename.
```
q-table-learned.json
```

It learned data is stored in JSON format, and it is a readabile text file containing a list of state-action pairs. We can read the file to understand how the AI makes its decision. For example:
```
q-table-learned.json
    ...
    "[<  v],[-1,+0,+0]": [
        -1.9256617062962396,
        1.6245052987863142,
        4.672521001106912
    ],
    ...
```
The above shows a record of state-action pair, where at this state, the food is at the south-west direction (as in `["<  v"]`), and the snake can see an obstacle (-1) on the left but clear (+0) in front and on the right (as in `[-1,+0,+0]`). The values to move left, front, right are -1.92, 1.62, 4.67 respectively. Based on Q-learning algorithm, the movement with the highest value will be picked, that is, moving right. Indeed, the snake has made an appropriate move.

## Trained Data (for DQN)
The trained data (i.e. weights) will be stored in the following file. If one already exists, it will be overwritten.
```
weights.hdf5
```

When launching, the program will read the following weight file. To use the previously trained data, simply rename it to the following filename.
```
weights-learned.hdf5
```

## Can DQN play a perfect game?
This is an interesting question. The following youtube video seems to have the answer. The video explains the design of the system state and demonstrates the AI playing a perfect game with design:
https://www.youtube.com/watch?v=vhiO4WsHA6c
