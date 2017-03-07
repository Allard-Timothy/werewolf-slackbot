"""Main App to process messages from 
"""
import time
import math
import yaml
import json
import copy

import random
from collections import defaultdict
import change_state

from router import command_router

from send_message import send_message


def process_message(data, game_state=None):
    """Process messages from players and from the game actions."""
    message = data.get('text', '')

    if message.startswith('!'):
        if not game_state:
            game_state_copy = copy.deepcopy(change_state.get_game_state())
        else:
            game_state_copy = copy.deepcopy(game_state)

        game_action = message[1:].split(" ")
        game_response, channel = command_router(game_state_copy, game_action, data['user'])

        if channel:
            send_message(game_response, channel)
        else:
            send_message(game_response)

        return game_response

    return None
