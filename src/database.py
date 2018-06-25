# The database class delivers data between the bot and the actual database

class database:

    def __init__(self):
        self.members = {}
        self.chat = {}

    # {
    #     "type": "team_join",
    #     "user": {
    #     "id": "U023BECGF",
    #     "name": "bobby",
    #     "deleted": false,
    #     "color": "9f69e7",
    #     "profile": {
    #         "first_name": "Bobby",
    #         "last_name": "Tables",
    #         "real_name": "Bobby Tables",
    #         "email": "bobby@slack.com"
    #     },
    #     "is_admin": true,
    #     "is_owner": true,
    #     "is_primary_owner": true,
    #     "is_restricted": false,
    #     "is_ultra_restricted": false,
    #     "has_2fa": false,
    #     "two_factor_type": "sms"
    #     }
    # }

    # add a user to the members
    def add_users(self, event):
        self.members[event["id"]] = event["name"]

    # save users in the members dictionary to the form of ["id": displayname]
    def record_users_list(self, team_info):
        for member in team_info["members"]:
            if member["is_bot"] == True:
                self.members[member["id"]] = member["name"]
            else:
                if member["profile"]["display_name"] == "":
                    self.members[member["id"]] = member["real_name"]
                else:
                    self.members[member["id"]] = member["profile"]["display_name"]

    # find user by id
    def find_user_by_id(self, user_id):
        if user_id in self.members.keys():
            return self.members[user_id]
        else:
            return None

    # get all user id from the team member list
    def get_all_users_id(self):
        return list(self.members.keys())

    # archieve a single message in a channel
    def archieve_msg(self, event):
        return None

    def __str__(self):
        return str(self.members)
