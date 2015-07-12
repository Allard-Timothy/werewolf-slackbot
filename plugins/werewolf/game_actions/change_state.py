"""
" all game state change
" in here.
"""

class GameLog:
    def __init__(self):
        """
        states is an ordered list of game states.
        """
        self.states = []

# initial game state.
GAME_STATE = {'players': {},
            'votes':{},
            'STATUS': 'INACTIVE',
            'ROUND': None}

game_log = GameLog()




def get_game_state():
    return GAME_STATE

def set_game_state(new_game_state):
    global GAME_STATE
    # set game state
    GAME_STATE = new_game_state


def update_game_state(g, action, **kwargs):
    """
    Only place we are allowed to change game state.
    If we save an ordered list of all game states,
    it'd be possible to undo/redo all steps. And do automated replays.

    ex. Game State N: [G0, G1, G2, G3... Gn]
    Every time this gets called could put it in redis.

    actions:
        'player_status'
        'vote'
        'join'
        'status'
        'round'
        'reset_votes'
        'reset_game_state'
    """
    def change_player_status():
        target = kwargs['player']
        new_status = kwargs['status']
        mutated_g[target]['status'] = new_status

    def add_vote():
        voter, votee = kwargs['voter'], kwargs['votee']
        mutated_g['votes'][voter] = votee

    def player_join():
        joined_player = kwargs['player']
        mutated_g['players'][joined_player] = {}

    def change_status():
        new_status = kwargs['status']
        mutated_g['STATUS'] = new_status
    def change_round():
        new_round = kwargs['round']
        mutated_g['ROUND'] = new_round
    def reset_votes():
        new_votes = {}
        mutated_g['votes'] = new_votes
    def reset_game():
        mutated_g = reset_game_state()

    mutated_g = g

    if action=='player_status':
        change_player_status()
    elif action=='join':
        player_join()
    elif action=='vote':
        add_vote()
    elif action=='status':
        change_status()
    elif action=='round':
        change_round()
    elif action=='reset_votes':
        reset_votes()
    elif action=='reset_game_state':
        reset_game()

    set_game_state(mutated_g)

    print(mutated_g) # for debugging.
    game_log.states.append(mutated_g)

    return mutated_g

def reset_game_state():
    """
    Returns an empty game state object.
    """
    return {'players': {},
            'votes':{},
            'STATUS': 'INACTIVE',
            'ROUND': None}