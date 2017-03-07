"""
All game actions.
"""
from change_state import update_game_state, get_game_state
from send_message import send_message
import random
import copy
from collections import Counter
import time

from user_map import UserMap, get_user_name
from validations import mod_valid_action, is_valid_action

from status import (players_in_game,
                    player_in_game,
                    is_player_alive,
                    alive_for_village,
                    alive_for_werewolf,
                    for_werewolf,
                    player_role,
                    player_side,
                    player_status,
                    has_voted,
                    did_everyone_vote,
                    get_all_alive,
                    get_all_votes,
                    get_current_round,
                    does_have_night_action)


u = UserMap()


def list_players(game_state, user_id, *kwargs):
    """List all the current players in the game."""
    user_map = UserMap()
    players = players_in_game(game_state)

    return '\n'.join([user_map.get(user_id=player_id) + ' | ' + player_status(game_status, player_id) for player_id in players]), None


def list_votes(game_state, *kwargs):
    """List all votes from players int he game."""
    votes = get_all_votes(game_state)

    out_list = []
    if votes:
        user_map = UserMap()
        for voter_id in votes.keys():
            voter_name = user_map.get(user_id=voter_id)
            votee_name = user_map.get(user_id=votes[voter_id])

            if votee_name:
                vote_mess = voter_name + ' voted ' + votee_name
            else:
                vote_mess = voter_name + ' passed'

            out_list.append(vote_mess)

        return '\n'.join(out_list), None

    return 'Cannot list votes now', None


def annoy():
    check_bool, msg = check()

    if not check_bool:
        return msg, None

    print('hi')


def start_countdown(game_state, user_id, *kwargs):
    """Start a countdown when it's day time in order to push inactive players to vote.
    We'll send them an annoyance ping and then `pass` their vote if they don't vote. 
    """
    import threading

    def check():
        check_game = get_game_state()

        result, message = mod_valid_action(user_id, 'countdown', check_game)
        if not result:
            return False, message

        all_alive = get_all_alive(game_state)
        yet_to_vote_list = [player_id for player_id in all_alive if not has_voted(game_state, player_id)]
        if len(yet_to_vote_list) > 1:
            return False, 'Countdown cannot start now.'

        yet_to_vote = yet_to_vote_list[0]
        return True, yet_to_vote

    def callback_vote():
        check_bool, yet_to_vote = check()
        if check_bool:
            check_game = get_game_state()
            send_message(player_vote(check_game, yet_to_vote, ['vote', 'pass'])[0])

    check_bool, message = check()
    if not check_bool:
        return message, None

    message_str = 'Countdown started. 60 seconds left.\n ' + u.get(user_id=msg) + ' please vote. Or your vote will be passed.'

    t = threading.Timer(60.0, callback_vote)
    t.start()

    return message_str, None


def create_game(game_state, user_id, *kwargs):
    """Create a new werewolf game, reset the game_state of previous games, and announce
    that we're waiting for players to join. Set game status as `WAITING_FOR_JOIN`
    """
    result, message = mod_valid_action(user_id, 'create', game_state)

    if result:
        if game_state['STATUS'] != 'INACTIVE':
            return 'Can not create new game.', None

        new_game = update_game_state(game_state, 'reset_game_state')
        new_game = update_game_state(new_game, 'status', status='WAITING_FOR_JOIN')

        return 'Waiting for players... \n*Type !join to join.*', None

    else:
        return message, None


def start_game(game_state, user_id, *kwargs):
    """Start the game and set game status to `RUNNING`."""
    result, message = mod_valid_action(user_id, 'start', game_state)
    if not result:
        return message, None

    send_message("@channel: Game is starting...")
    players = players_in_game(game_state)
    num_werewolves = werewolf_in_game(game_state)

    p1_str = "_There are *%d* players in the game._\n" % len(players)
    p2_str = "There are *%d* werewolves in the game._\n" % len(num_werewolves)
    send_message(p1_str + p2_str)

    game_state = update_game_state(game_state, 'status', status='RUNNING')

    new_game = assign_roles(game_state)
    message_everyone_roles(new_game)

    return start_day_round(new_game), None


def assign_roles(game_state):
    """Assign all players in the game a role."""
    total_players = players_in_game(game_state)

    # 3 or fewer wolves for 11 - 23 players
    if len(total_players) >= 11 and len(total_players) < 23:
        wolf_div = 4

    # more than 3 wolves for 23+ players
    elif len(total_players) >= 23:
        wolf_div = 3

    num_of_wolfs = int(len(total_players) / wolf_div)

    created_wolves = random.sample(total_players, num_of_wolfs)
    created_villas = [player for player in total_players if player not in created_wolves]

    new_game = copy.deepcopy(game_state)

    for villa in created_villas:
        new_game = update_game_state(new_game, 'role', player=villa, role='v')

    for wolf in created_wolves:
        new_game = update_game_state(new_game, 'role', player=wolf, role='w')

    return new_game


def message_everyone_roles(game_state):
    """Ping players with their roles."""
    user_map = UserMap()

    role_message_mapping = {
        'v': " Plain Villager",
        'w': " Werewolf Awoooo!",
        's': " Seer",
        'a': " Angel"
    }

    def _player_tuple(player_id, game_state):

        return (user_map.get(user_id=player_id, DM=True), player_role(game_state, player_id))

    all_alive = [_player_tuple(player_id, game_state) for player_id in players_in_game(game_state) if is_player_alive(game_state, player_id)]

    for im, role in all_alive:
        dm_message = role_message_mapping[role]
        send_message(dm_message, channel=im)


def join(game_state, user_id, *args):
    """Join the game if the player hasn't joined yet."""
    result, message = mod_valid_action(user_id, 'join', game_state)

    if not result:
        return message, None

    user_map = UserMap()
    user_name = user_map.get(user_id=user_id)

    if not user_name:
        user_name = get_user_name(user_id)

    new_game_w_new_player = update_game_state(game_state, 'join', player=user_id)

    join_message = "%s joined the game." % user_name
    return join_message, None


def eat_player(game_state, user_id, *args):
    """Night kill the selected player."""
    arg_list = args[0]

    if len(arg_list) < 1: # no target no good
        return "Have to pick a target.", None
    elif len(arg_list) > 2: # too many args
        return "Not a valid command.", None
    else:
        u = UserMap() # get usermap

        target_name = arg_list[1]
        target_id =  u.get(name=target_name) # turn name into id
        result, message = is_valid_action(user_id, 'kill', g, target_name=target_name)
        if not result:
            # was not a valid kill
            return message, None
        else:
            # player is eaten
            # update state
            # changes targeted player's status to dead
            new_g = update_game_state(g, 'player_status', player=target_id, status='dead')
            # tell the players.
            eaten_str = "%s was eaten." % (target_name)
            return resolve_night_round(new_g, alert=eaten_str), None


def seer_peek_player(g, user_id, *args):
    """
    Player attemps to investigate.

    If is seer & night. returns message, channel is Direct Message to seer.

    ex. *args = (['seer', 'maksym'], )
    arg_list = args[0]
    target_name = args[1]
    """
    arg_list = args[0]

    if len(arg_list) < 1: # no target no good
        return "Have to pick a target.", None
    elif len(arg_list) > 2: # too many args
        return "Not a valid command.", None
    else:
        target_name = arg_list[1]
        target_id = u.get(name=target_name)
        #result, message = is_valid_action(user_id, 'seer', g, target_name=target_name)
        return 'Not Implemented', None


def make_end_round_str(g, alert=None, game_over=None):
    """
    g - game state
    alert - string of any alerts
    game_over - string of role that won, if game is over.
    """
    round_end_str = ''

    if alert:
        round_end_str += alert

    if game_over:
        if game_over == 'w':
            # werewolves won
            round_end_str += "\n Game Over. Werewolves wins.\n"

        elif game_over == 'v':
            # village wins
            round_end_str += "\n Game Over. Village wins.\n"

        # Display list of players and their roles
        round_end_str += '\n'.join(
                [u.get(user_id=p_id) + "%s | *%s*." % (u.get(user_id=p_id), player_role(g, p_id))
                    for p_id in players_in_game(g)])

    return round_end_str


def resolve_night_round(g, alert=None):
    """
    Makes sure everyone has done all their roles.

    - if yes
        see if game is over.
        if yes
            set game to over.
            display results.
        if no
            change round to day.
    """
    # TODO:  for each player in the game,
    # check if completed their action for the night.

    alive_v = alive_for_village(g)
    alive_w = alive_for_werewolf(g)

    if len(alive_w) >= len(alive_v):
        new_g = update_game_state(g, 'status', status='INACTIVE')
        # reset game state.
        new_g = update_game_state(new_g, 'reset_game_state')

        return  make_end_round_str(new_g, alert, 'w') # returns and sends message
    elif len(alive_w) == 0:
        new_g = update_game_state(g, 'status', status='INACTIVE')
        # reset game state.
        new_g = update_game_state(new_g, 'reset_game_state')

        return make_end_round_str(new_g, alert, 'v') # returns and sends message
    else:
        # turn it into morning and start day round.

        # idea:
        # game state has 'GAME_MESSAGES' : {'channel': <channel_id>, 'message': thing to say}
        # every night action adds game_message.
        # If all night actions have finished. Go through and send all those messages.
        # reset GAME_MESSAGES.

        round_end_str = make_end_round_str(g) + start_day_round(g)

        return round_end_str



def start_night_round(g):
    """
    1.) Set state to night round.
    2.) For each player,
        if it is a character without a night action (ie. 'v'):
            set completed_night_action: True
            else completed_night_action: False
    3.) Send night message.
    """
    all_alive = get_all_alive(g)

    new_g = update_game_state(g, 'round', round='night')

    for player_id in all_alive:
        new_g = update_game_state(new_g,
                    'change_night_action_status',
                    player=player_id,
                    completed_night_action=does_have_night_action(g, player_id))

    return "It is night time. \n Werewolf type_'/dm moderator !kill {who you want to eat}_ \n\n *Talking is NOT Allowed.*"


def start_day_round(g):
    update_game_state(g, 'round', round='day')
    return "It is now day time. \n type _!vote {username}_. If user has more than half the votes. They die."


def player_vote(g, user_id, *args):
    """
    ex. *args = (['vote', 'maksym'], )
    arg_list = args[0]
    target_name = arg_list[1]


    user_name = u.id_dict.get(user_id)

    """
    arg_list = args[0]

    if len(arg_list) < 1: # didn't vote
        return "Have to vote FOR someone.", None
    elif len(arg_list) > 2: # too many args
        return "Not a valid command.", None
    else:
        target_name = arg_list[1]
        target_id =  u.get(name=target_name) # turn name into id

        result, message = is_valid_action(user_id, 'vote', g, target_name=target_name)
        if not result:
            # was not a valid kill
            return message, None
        else:
            # player voted
            # update state
            # change votes to reflect their vote
            new_g = update_game_state(g, 'vote', voter=user_id, votee=target_id)

            # after each vote need to check if total
            # everyone has voted.
            if did_everyone_vote(new_g):
                # resolve vote round
                result_id = resolve_votes(new_g)
                if result_id:
                    # result is id of player
                    # set player status to dead.
                    result_name = u.get(user_id=result_id)

                    new_g_2 = update_game_state(new_g, 'player_status', player=result_id, status='dead')
                    # have to reset all the votes
                    new_g_3 = update_game_state(new_g_2, 'reset_votes')

                    # tell the players.
                    lynch_str = "%s was lynched." % (result_name)
                    # pass in game state before votes reset.
                    return resolve_day_round(new_g_2, alert=lynch_str), None

                else:
                    # list votes returns a tuple ('str', None)
                    return resolve_day_round(new_g, alert='*No one dies.*'), None
            else:
                # valid vote, but not everyone voted yet.
                # suggestion to list vote summary every vote.
                return list_votes(new_g)[0] + '\n\n' + message
            return message, None

def resolve_votes(g):
    """
    Everyone has voted.

    If anyone has more than half the votes.
    They die.

    If more than half the people passed then no one dies.

    votes is a dictionary
    key   - voter_id
    value - voted_on_id
    """
    votes = get_all_votes(g)
    # count up all the votes
    if votes:
        c = Counter(votes.values())
        # c.most_common()
        # [('b',2), ('a',1), ('c',1)]
        most_votes_id = c.most_common()[0][0]
        most_votes_count = c[most_votes_id]
        total_votes = len(votes.keys())
        if most_votes_count > total_votes // 2:
            # more than half the votes
            # they die.
            if most_votes_id == 'pass':
                return False # no one dies
            else:
                return most_votes_id

        else:
            return False

    return False # votes was none for some reason.



def resolve_day_round(g, alert=None):
    """
    Like resolve_night_round, but for the day!

    """
    alive_v = alive_for_village(g)
    alive_w = alive_for_werewolf(g)

    # we want to show vote results.
    vote_list_str = list_votes(g)[0] + '\n'

    if len(alive_w) >= len(alive_v):
        new_g = update_game_state(g, 'status', status='INACTIVE')
        new_g = update_game_state(new_g, 'reset_game_state')

        return  vote_list_str + make_end_round_str(new_g, alert, 'w') # returns and sends message

    elif len(alive_w) == 0:
        new_g = update_game_state(g, 'status', status='INACTIVE')
        new_g = update_game_state(new_g, 'reset_game_state')

        return  vote_list_str + make_end_round_str(new_g, alert, 'v') # returns and sends message
    else:
        # turn it into night and start night round

        round_end_str = vote_list_str + make_end_round_str(g) + start_night_round(g)
        return round_end_str


