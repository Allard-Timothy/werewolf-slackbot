"""
Game status functions

"""


def players_in_game(game_state):
    return game_state['players'].keys()


def player_in_game(game_state, user_id):
    """return if a player is in the game."""
    return user_id in players_in_game(game_state)


def is_player_alive(game_state, user_id):
    """is the given player alive?"""
    status = game_state['players'].get(user_id).get('status')
    if status == 'alive':
        return True
    elif status == 'dead':
        return False
    else:
        print('durr')


def alive_for_village(game_state):
    players = players_in_game(game_state)
    return [player_id for player_id in players if is_player_alive(game_state, player_id) and player_side(game_state, player_id)=='v']


def alive_for_werewolf(game_state):
    players = players_in_game(game_state)
    return [player_id for player_id in players if is_player_alive(game_state, player_id) and player_side(game_state, player_id)=='w']


def for_werewolf(game_state):
    players = players_in_game(game_state)
    return [player_id for player_id in players if player_side(game_state, player_id=='w')]


def player_role(game_state, user_id):
    return game_state['players'].get(user_id).get('role')


def player_side(game_state, user_id):
    return game_state['players'].get(user_id).get('side')


def player_status(game_state, user_id):
    return game_state['players'].get(user_id).get('status')


def has_voted(game_state, user_id):
    """ check if the given user has voted."""
    return user_id in game_state['votes'].keys()


def did_everyone_vote(game_state):
    """did everyone vote?"""
    alive = get_all_alive(game_state)

    alive_and_voted = [player_id for player_id in alive if has_voted(game_state, player_id)]

    return len(alive_and_voted) == len(alive)


def get_all_alive(game_state):
    return [player_id for player_id in players_in_game(game_state) if is_player_alive(game_state, player_id)]


def does_have_night_action(game_state, user_id):
    """players with night actions

    w: werewolf (or just alpha wolf)
    s: seer
    a: angel
    """
    night_action_list = ['w', 's', 'a']
    return player_role(game_state, user_id) in night_action_list


def get_all_votes(game_state):
    """All the votes."""
    if get_current_round(game_state) != 'day':
        return None
    elif game_state['STATUS'] == 'INACTIVE':
        return None

    return game_state.get('votes')


def get_current_round(game_state):
    """is it night or day?"""
    return game_state['ROUND']
