# main body of bot

import os
import time
import re
import json
import bluemix_tone as BT
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from slackclient import SlackClient
from database import database

bot_id = None
RTM_READ_DELAY = 1
DEFAULT_NUM_OF_MSG = 100
EXAMPLE_COMMAND = "help"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
OAUTH_ACCESS_TOKEN = os.environ.get('OAUTH_ACCESS_TOKEN')
database = database()
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def presence_query(channel):
    id_list = database.get_all_users_id()
    print("id_list is: {}".format(id_list))
    query = json.dumps({"type": "presence_query","ids": id_list})
    print("hello: {}".format(slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=query
        )))

# retrieve current users list in a team
def get_team_info():
    team_info = slack_client.api_call("users.list")
    # if the call returns users list
    if team_info["ok"]:
        # print("Regular check users list {}".format(team_info))
        database.record_users_list(team_info)
    else:
        print("team_info: {}".format(team_info))
        print("WARNING: Problem retrieving users lsit.")

# determines the events type
def parse_events(slack_events):

    for event in slack_events:
        # event of message
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == bot_id:
                print("message found")
                sender_id = event["user"]
                return message, event["channel"], sender_id
        # # event of team_join
        # elif event["type"] == "team_join":
        #     database.add_users(event)
    return None, None, None


# retrieve message receiver
def parse_direct_mention(message_text):
    matches = re.search(MENTION_REGEX, message_text)
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

# get channel chat history
def get_chat_history(channel, latest=time.time(), oldest=None, num_of_msg=DEFAULT_NUM_OF_MSG):
    response = slack_client.api_call( 
                "channels.history",
                channel=channel,
                count=num_of_msg + 1,
                # latest=latest,
                # oldest=oldest,
                token=OAUTH_ACCESS_TOKEN
                )
    if response["ok"]:
        messages = []
        for t in response["messages"]:
            if "subtype" in t:
                continue
            if t["text"].startswith("<@{}>".format(bot_id)):
                continue
            messages.append(t["text"])
        # remove @userid in messages
        print("messages {}".format(messages))
        print("\nnumber of actual messages: {}".format(len(messages)))
        return messages
    else:
        print (response)
        print("Error: Didn't get any chat history.")
        return "None"

# excute command
def handle_command(command, channel, sender_id):
    print("this is channel {}".format(channel))
    default_responses = "Not sure what you mean, Try *{}*.". format(EXAMPLE_COMMAND)
    response = None
    # handle user requiring summary
    if command.startswith("/summary"):
        params = command.split(" ")[1:]
        vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1, 1), min_df=0, stop_words='english')
        # keywords by cound
        if len(params) == 1 and params[0].isdigit():
            messages = get_chat_history(channel, num_of_msg=int(params[0]))
            if len(messages) != 0:
                tfidf = vectorizer.fit_transform(messages)
                docId_featureId_tuple = [(tfidf.nonzero()[0][i],tfidf.nonzero()[1][i]) for i in range(len(tfidf.nonzero()[0]))]
                features = vectorizer.get_feature_names()
                rev_dic = dict([(feature, []) for feature in features])
                for docId, featureId in docId_featureId_tuple:
                    rev_dic[features[featureId]].append(docId)
                # print("------\nrev_dic {}".format(rev_dic))
                # print("------\ntfidf {}".format(tfidf))
                # print("------\ntuple {}".format(docId_featureId_tuple))
                # print("------\nfeature_names {}".format(features))
                # print("------\nasarray {}".format(np.asarray(tfidf.sum(axis=0)).ravel()))
                scores = zip(features, np.asarray(tfidf.sum(axis=0)).ravel())
                sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
                # print("------\nsorted_scores {}".format(sorted_scores))
                response = "This is a summary of your last *{0}* messages in channel <{1}>:\n".format(params[0], channel)
        
        # keywords by time, 
        
        # keywords by default
        
                for index, item in enumerate(sorted_scores):
                    if index < 25:
                        response += "*{0}*. {1}\n".format(index + 1, item[0])
                        for docId in rev_dic[item[0]]:
                            # find the words in doc
                            words = messages[docId].split()
                            # match he keywords in sentences
                            for ind,x in enumerate(words):
                               if re.match("^(\W)*{}(\W)*$".format(item[0]), x, re.IGNORECASE):
                                   response += "\t{}\n".format(" ".join(words[ind-3:ind]+words[ind:ind+4]))
                        response += "\n"
                    else:
                        break
            else:
                response = "There's no real messages in the last *{}* messages".format(params[0])
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response
            )

    else:
        # handle general instructions
        user_tones = BT.parse_blumix_feedback(BT.semantic_analyze(command))
        response = "<@{}>...{}!".format(sender_id, BT.to_str(user_tones))
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_responses
            )


if __name__ == "__main__":

    print ("Start running.")
    if slack_client.rtm_connect(with_team_state=False):
        print("SUCCESS:Bot connected and running!")
        bot_id = slack_client.api_call("auth.test")["user_id"]


        print("Bot id: {}".format(bot_id))
        get_team_info()
        # presence_query()
        print(database)
        run_it_once = True

        while True:
            command, channel, sender_id = parse_events(slack_client.rtm_read())
            if channel:
                members = slack_client.api_call("conversations.members", channel=channel)["members"]
                if run_it_once:
                    # presence_query(channel)
                    run_it_once = False
            if command:
                handle_command(command, channel, sender_id)
            time.sleep(RTM_READ_DELAY)
    else:
        print("WARNING: Connection failed. Exception tracebak printed above.")