#!/usr/bin/python

import time
import json
import Pyro.core


def main(movement):
    id = 1000
    while True: 
        world  = movement.all()
        print json.dumps(world)

        time.sleep(0.10)

movement = Pyro.core.getProxyForURI("PYRONAME://robotmovement")

main(movement)

