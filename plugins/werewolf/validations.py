"""
Validate that any actions taken in game can be perfomed and process accordingly.
"""


from change_state import update_game_state
import status
from user_map import UserMap


RESPONSE = {
        'already_joined': "You have already joined game",
        'already_voted': "You have already voted",
        'not_waiting': "Game isn't waiting for players to join",
        'num_players': 'Nope, there is not enough players to start',
        'not_day': "Sorry dawg, it's not day",
        'not_night': "It is not night",
        'no_countdown': "Sorry, cannot start the countdown now",
        'invalid': "Sorry, invalid command",
        'u_not_in_game':"Sorry, doesn't look like you are in the game",
        'u_not_alive': "You are no longer alive",
        't_not_alive': "Your target is no longer alive",
        't_not_in_game': "Your target is not in the game",
        'user_n_in_game': "Sorry, user isn't in the game",
        'not_wolf': "You are not a wolf",
        'pass': " is passing on their vote",
        'noop': "Not allowed",
        'invalid': "Invalid Action",
        'need_target': "Need a target",
        'dead_villa': "Dead villas cannot perform peeks",
        'dead_wolf': "Dead wolves cannot perform kills",
        'peek': "{target_name}'s role is {role}",
        'not_seer': "Only the seer may request peeks"
    }


def should_create_game(user, action, game_state):
    """Create a new game."""
    return True, None


def should_start_game(user_id, action, game_state):
    """Check if we should start a new game"""
    players = status.players_in_game(game_state)
    print players
    print game_state

    # min for a good game is 11
    if len(players) < 1:
        return False, RESPONSE['num_players']

    if game_state.get('STATUS') != 'WAITING_FOR_JOIN':
        return False, RESPONSE['not_waiting']

    return True, None


def should_user_join_game(user_id, action, game_state):
    """Check if user can join game."""
    if game_state.get('STATUS') != 'WAITING_FOR_JOIN':
        return False, RESPONSE['not_waiting']

    if status.player_in_game(game_state, user_id):
        return False, RESPONSE['already_joined']

    return True, None


def should_countdown(user_id, action, game_state):
   """Check if we can start a countdown. To do so it must be day and the command must come
   from a player in the game.
   """
   if status.get_current_round(game_state) != "day":
       return False, RESPONSE['not_day']

   elif not status.is_player_alive(game_state, user_id):
       return False, RESPONSE['no_countdown']

   elif len(status.get_all_alive(game_state)) - 1 == len(status.get_all_votes(game_state).keys()):
       return True, None

   else:
       return False, RESPONSE['no_countdown']


def vote(user_id, action, game_state, target_name):
    user_map = UserMap()
    target_id = user_map.get(name=target_name)
    user_name = user_map.get(user_id)

    if not status.player_in_game(game_state, user_id):
        return False, RESPONSE['u_not_in_game']

    if not status.is_player_alive(game_state, user_id):
        return False, RESPONSE['u_not_alive']

    if status.get_current_round(game_state) != 'day':
        return False, RESPONSE['not_day']

    if target_name == 'pass':
        return True, user_name + RESPONSE['pass']

    if not status.player_in_game(game_state, target_id):
        return False, RESPONSE['t_not_in_game']

    if not status.is_player_alive(game_state, target_id):
        return False, RESPONSE['t_not_alive']

    if status.has_voted(game_state, user_id):
        return True, user_name + ' changed vote to ' + '*' + target_name + '*'

    return True, user_name + ' voted for ' + '*' + target_name + '*'


def night_kill(user_id, action, game_state, target_name):
    user_map = UserMap()
    target_id = user_map.get(name=target_name)
    user_name = user_map.get(user_id)

    if not status.player_in_game(game_state,user_id):
        return False, RESPONSE['noop']

    if status.player_role(game_state, user_id) != 'w':
        return False, RESPONSE['noop']

    if not status.is_player_alive(game_state, user_id):
        return False, 'Dead wolves can not kill.'

    if status.get_current_round(game_state) != 'night':
        return False, RESPONSE['noop']

    if not status.player_in_game(game_state, target_id):
        return False, RESPONSE['noop']

    if not status.is_player_alive(game_state, target_id):
        return False, RESPONSE['noop']

    return True, ""


def peek(user_id, action, game_state, target_name):
    user_map = UserMap()
    target_id = user_map.get(name=target_name)
    user_name = user_map.get(user_id)

    if not status.player_in_game(game_state,user_id):
        return False, RESPONSE['noop']

    if not status.is_player_alive(game_state, user_id):
        return False, RESPONSE['dead_villa']

    if status.player_role(game_state, user_id) == 's':
        return False, RESPONSE['noop']

    if status.get_current_round(game_state) != 'night':
        return False, RESPONSE['noop']

    if status.player_role(game_state, user_id) != 's':
        return False, RESPONSE['not_seer']

    target_role = status.player_role(game_state, target_name)

    return True, RESPONSE['peek'].format(target_name, target_role)


MOD_ACTION_MAPPING = {
    'create': should_create_game,
    'start': should_start_game,
    'join': should_user_join_game,
    'countdown': should_countdown
}

PLAYER_ACTION_MAPPING = {
    'night_kill': night_kill,
    'vote': vote,
    'peek': peek,
}


def mod_valid_action(user_id, action, game_state):
    """Mod actions to manage and facilitate game_state.

    Mod actions:
      `create`
      `start`
      `join`
      `countdown`
    """
    action_response_fn = MOD_ACTION_MAPPING.get(action, None)

    if action_response_fn:
        return action_response_fn(user_id, action, game_state)

    return False, RESPONSE['invalid']


def is_valid_action(user_id, action, game_state, target_name=None):
    """Determine if the provided in-game player action should be executed or not.

    In-game player actions:
      `vote`
      `night_kill(wolf night aciton)`
      `peek(seer night action)`
      `save(angel night action)`
    """
    user_map = UserMap()

    if not target_name:
        return False, RESPONSE['need_target']

    if user_map:
        target_id = user_map.get(name=target_name)
        user_name = user_map.get(user_id)

        if not target_id and target_name != 'pass':
            return False, RESPONSE['user_n_in_game']

    player_action_fn = PLAYER_ACTION_MAPPING.get(action, None)
    if player_action_fn:
        return player_action_fn(user_id, action, game_state, target_name)

    return False, RESPONSE['invalid']
