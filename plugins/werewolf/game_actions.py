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

import status



def list_players(game_state, user_id, *kwargs):
    """List all the current players in the game."""
    user_map = UserMap()
    players = status.players_in_game(game_state)

    return '\n'.join([user_map.get(user_id=player_id) + ' | ' + status.player_status(game_state, player_id) for player_id in players]), None


def list_votes(game_state, *kwargs):
    """List all votes from players int he game."""
    votes = status.get_all_votes(game_state)

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
    user_map = UserMap()

    def check():
        check_game = get_game_state()

        result, message = mod_valid_action(user_id, 'countdown', check_game)
        if not result:
            return False, message

        all_alive = status.get_all_alive(game_state)
        yet_to_vote_list = [player_id for player_id in all_alive if not status.has_voted(game_state, player_id)]
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

    message_str = 'Countdown started. 60 seconds left.\n ' + user_map.get(user_id=message) + ' please vote. Or your vote will be passed.'

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
    players = status.players_in_game(game_state)
    num_werewolves = status.alive_for_werewolf(game_state)

    p1_str = "_There are *%d* players in the game._\n" % len(players)
    p2_str = "There are *%d* werewolves in the game._\n" % len(num_werewolves)
    p3_str = "https://media.giphy.com/media/3o72FkgwrI7P4G1amI/giphy.gif"
    send_message(p1_str + p2_str + p3_str)

    game_state = update_game_state(game_state, 'status', status='RUNNING')

    new_game = assign_roles(game_state)
    message_everyone_roles(new_game)

    return start_day_round(new_game), None


def assign_roles(game_state):
    """Assign all players in the game a role."""
    total_players = status.players_in_game(game_state)
    num_of_wolves = 1
    num_of_players = len(total_players)
    seer = None
    angel = None

    # if it's only 2 players that's lame, but at least make them on diff teams
    if num_of_players <= 2:
        if num_of_players == 1:
            villas = total_players[0]

        else:
            villas = total_players[0]
            wolves = total_players[1]

    if num_of_players > 2:
        if num_of_players >= 1 and num_of_players < 13:
            num_of_wolves = 2

        elif num_of_players >= 13 and num_of_players < 23:
            num_of_wolves = 3

        elif num_of_players >= 23:
            num_of_wolves = 6

        wolves = random.sample(total_players, num_of_wolves)
        non_wolves = [player for player in total_players if player not in created_wolves]

        ramdom.shuffle(non_wolves)

        seer = non_wolves[0]
        angel = non_wolves[1]
        villas = [x for x in non_wolves if x != seer and x != angel]

    new_game = copy.deepcopy(game_state)

    if seer and angel:
        new_game = update_game_state(new_game, 'role', player=seer, role='s')
        new_game = update_game_state(new_game, 'role', player=angel, role='a')

    for villa in villas:
        new_game = update_game_state(new_game, 'role', player=villa, role='v')

    for wolf in wolves:
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

        return (user_map.get(user_id=player_id, DM=True), status.player_role(game_state, player_id))

    all_alive = [_player_tuple(player_id, game_state) for player_id in status.players_in_game(game_state) if status.is_player_alive(game_state, player_id)]

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


def night_kill(game_state, user_id, *args):
    """Night kill the selected player."""
    arg_list = args[0]

    if len(arg_list) < 1:
        return "Have to pick a target.", None

    elif len(arg_list) > 2:
        return "Not a valid command.", None

    else:
        user_map = UserMap()

        target_name = arg_list[1]
        target_id =  user_map.get(name=target_name)
        result, message = is_valid_action(user_id, 'kill', game_state, target_name=target_name)
        if not result:
            return message, None

        else:
            new_game = update_game_state(game_state, 'player_status', player=target_id, status='dead')
            eaten_str = "%s was night killed." % (target_name)
            return resolve_night_round(new_game, alert=eaten_str), None


def seer_peek_player(game_state, user_id, *args):
    """Seer can peek a players role during the night."""
    user_map = UserMap()
    arg_list = args[0]

    if len(arg_list) < 1:
        return "Have to pick a target.", None

    elif len(arg_list) > 2:
        return "Not a valid command.", None

    else:
        target_name = arg_list[1]
        target_id = user_map.get(name=target_name)
        result, message = is_valid_action(user_id, 'peek', game_state, target_name=target_name)

        if not result:
            return message, None

        else:
            #TODO update game status that seer used peek and send message to seer
            pass


def make_end_round_str(game_state, alert=None, game_over=None):
    """Reconcile end of day actions and either enter night mode or end game."""
    user_map = UserMap()

    round_end_str = ''

    if alert:
        round_end_str += alert

    if game_over:
        if game_over == 'w':
            round_end_str += "\n Game Over. Werewolves wins.\n"

        elif game_over == 'v':
            round_end_str += "\n Game Over. Village wins.\n"

        def player_role_string(player_id, game_state):
            return user_map.get(user_id=player_id) + "%s | %s" % (user_map.get(user_id=player_id), status.player_role(game_state, player_id))

        status.player_roles = [player_role_string(player_id, game_state) for player_id in status.players_in_game(game_state)]
        round_end_str += '\n'.join(status.player_roles)

    return round_end_str


def resolve_night_round(game_state, alert=None):
    """Reconcile all night actions and update the game_state. The game can either continue into
    day mode or it will end with the night actions.
    """
    alive_v = status.alive_for_village(game_state)
    alive_w = status.alive_for_werewolf(game_state)

    if len(alive_w) >= len(alive_v):
        new_game = update_game_state(game_state, 'status', status='INACTIVE')
        new_game = update_game_state(new_game, 'reset_game_state')

        return  make_end_round_str(new_game, alert, 'w')

    elif len(alive_w) == 0:
        new_game = update_game_state(game_state, 'status', status='INACTIVE')
        new_game = update_game_state(new_game, 'reset_game_state')

        return make_end_round_str(new_game, alert, 'v')

    else:
        #TODO: aggregate of all night action game messages with channel id(dm) in game_state
        # and then send all messages at once
        round_end_str = make_end_round_str(game_state) + start_day_round(game_state)

        return round_end_str


def start_night_round(game_state):
    """Start the night round by setting all villas without a night action to completed, set all
    villas/wolves with a night action to false and send night action PM's
    """
    all_alive = status.get_all_alive(game_state)

    new_game = update_game_state(game_state, 'round', round='night')

    for player_id in all_alive:
        new_game = update_game_state(new_game,
                    'change_night_action_status',
                    player=player_id,
                    completed_night_action=status.does_have_night_action(game_state, player_id))

    return "It is night time. \n Werewolf type_'/dm moderator !kill {who you want to eat}_ \n\n *Talking is NOT Allowed.*"


def start_day_round(game_state):
    update_game_state(game_state, 'round', round='day')
    return "It is now day time. \n type _!vote {username}_. If user has more than half the votes. They die."


def player_vote(game_state, user_id, *args):
    """Update the game_state with a players lynch vote."""
    user_map = UserMap()
    arg_list = args[0]

    if len(arg_list) < 1:
        return "Have to vote FOR someone.", None

    elif len(arg_list) > 2:
        return "Not a valid command.", None

    else:
        target_name = arg_list[1]
        target_id =  user_map.get(name=target_name)

        result, message = is_valid_action(user_id, 'vote', game_state, target_name=target_name)
        if not result:
            return message, None

        else:
            new_game = update_game_state(game_state, 'vote', voter=user_id, votee=target_id)

            if status.did_everyone_vote(new_game):
                result_id = resolve_votes(new_game)

                if result_id:
                    result_name = u.get(user_id=result_id)

                    set_deaths_in_game_state = update_game_state(new_game, 'player_status', player=result_id, status='dead')
                    reset_game_votes = update_game_state(set_deaths_in_game_state, 'reset_votes')

                    lynch_str = "%s was lynched." % (result_name)
                    return resolve_day_round(set_deaths_in_game_state, alert=lynch_str), None

                else:
                    return resolve_day_round(new_game, alert='*No one dies.*'), None

            else:
                return list_votes(new_game)[0] + '\n\n' + message, None

            return message, None


def resolve_votes(game_state):
    """Reconcile all the votes, lynching the player with the majority of the votes."""
    votes = status.get_all_votes(game_state)

    if votes:
        count = Counter(votes.values())

        most_votes_id = count.most_common()[0][0]
        most_votes_count = count[most_votes_id]
        total_votes = len(votes.keys())

        if most_votes_count > total_votes // 2:
            if most_votes_id == 'pass':
                return False

            else:
                return most_votes_id

        else:
            return False

    # we shouldn't ever really get here
    return False


def resolve_day_round(game_state, alert=None):
    """Reconcile all votes for the day and enter night mode."""
    alive_v = status.alive_for_village(game_state)
    alive_w = status.alive_for_werewolf(game_state)

    vote_list_str = list_votes(game_state)[0] + '\n'

    if len(alive_w) >= len(alive_v):
        new_game = update_game_state(game_state, 'status', status='INACTIVE')
        new_game = update_game_state(new_game, 'reset_game_state')

        return  vote_list_str + make_end_round_str(new_game, alert, 'w')

    elif len(alive_w) == 0:
        new_game = update_game_state(game_state, 'status', status='INACTIVE')
        new_game = update_game_state(new_game, 'reset_game_state')

        return  vote_list_str + make_end_round_str(new_game, alert, 'v')

    else:
        return vote_list_str + make_end_round_str(game_state) + start_night_round(game_state)
