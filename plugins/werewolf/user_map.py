import redis
import yaml
import json
from slackclient import SlackClient


class UserMap:
    """
    Store all player infor in this user mapping class. That way we can pass this around as needed.
    """

    def __init__(self):
        self.r_server = redis.Redis('localhost')

    def add(self, user_id, name, DM):
        """Add a user to the UserMap, specifically the user name, user_id, and DM_id."""
        self.r_server.hmset('users:game', {user_id: name, name: user_id, 'DM:'+user_id: DM})

    def get(self, user_id=None, name=None, DM=None):
        if DM and user_id:
            return self.r_server.hmget('users:game', 'DM:'+user_id)[0]
        elif user_id:
            return self.r_server.hmget('users:game', user_id)[0]
        elif name:
            return self.r_server.hmget('users:game', name)[0]
        else:
            return None


def get_user_name(user_id):
    config = yaml.load(file('rtmbot.conf', 'r'))
    sc = SlackClient(config['SLACK_TOKEN'])
    user_map = UserMap()

    def get_users_from_slack():
        user_obj = sc.api_call('users.info', user=user_id)
        user_name = user_obj['user']['name']
        im = sc.api_call('im.open', user=user_id)

        return user_name, im['channel']['id']

    try:
        user_name, im = get_users_from_slack()
    # we really dont want any issues with the slack API to blow up the game
    except Exception as e:
        user_name, im = get_users_from_slack()

    if user_name:
        user_map.add(user_id, user_name, im)
        return user_name
