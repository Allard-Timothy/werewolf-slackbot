import game_actions

INVALID_COMMAND = 'Not a valid command!'


def command_router(game_state, command, user_id):
    """Handle commands from the players of the game. This will call a particular game action to
    execute the given command from the player.

    `game_state` - game state object
    `command` - list [command, args]
    `user_id` - user that issued command

    create(create_game)  - create a new game (starts moderator- alerts channel)
    join(player_join)    - player attempts to join a created game
    start(start_game)    - starts game, assigns roles, other setup.
    players(list_players)- list players in the game.
    votes(list_votes)    - list all the votes in the game.
    countdown(start_countdown) - intitiate vote pass to lame player.

    --- Game Actions ---
    kill(night_kill)   - werewolf attempts to eat a player
    vote(player_vote)  - players attempts to vote.
    """
    router = {
        "create": game_actions.create_game,
        'start': game_actions.start_game,
        'players': game_actions.list_players,
        'votes': game_actions.list_votes,
        "join": game_actions.join,
        "countdown": game_actions.start_countdown,

        "peek": game_actions.seer_peek_player,
        "eat": game_actions.night_kill,
        "vote": game_actions.player_vote
    }

    if len(command) == 1:
        command_word = command[0]
        action_fn = router.get(command_word)

        if action_fn:
            return action_fn(game_state, user_id, command_word)
        else:
            return INVALID_COMMAND, None

    elif len(command) > 1:
        command_word = command[0]
        action_fn = router.get(command_word)
        if action_fn:
            return action_fn(game_state, user_id, command[0:])
        else:
            return INVALID_COMMAND, None

    else:
        return INVALID_COMMAND, None
