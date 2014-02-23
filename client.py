
#!/usr/bin/python

import time
import curses as c
import json
import Pyro.core
import sys

movement = Pyro.core.getProxyForURI("PYRONAME://robotmovement")

movement.move(0.0,0.0);

def doMove(args, movement):
    movement.move(float(args[0]), float(args[1]))

def doStop(args, movement):
    movement.move(0.0, 0.0)

funcs = {
    'move':doMove,
    'stop':doStop,
    }

if __name__=='__main__':
    command = sys.argv[1]
    args = sys.argv[2:]
    print command, args
    if command in funcs:
        funcs[command](args, movement)

