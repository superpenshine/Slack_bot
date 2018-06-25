
import os
import requests
import json

def semantic_analyze(text):
    username = os.environ.get("IBM_TONE_ANALYZE_NAME")
    password = os.environ.get("IBM_TONE_ANALYZE_PASSWORD")
    watsonUrl = 'https://gateway.watsonplatform.net/tone-analyzer/api/v3/tone?version=2017-09-21'
    headers = {"content-type": "text/plain"}
    try:
        r = requests.post(watsonUrl, auth=(username,password),headers = headers,
         data=text)
        return r.text
    except:
        return False

# {"document_tone": {"tones": [
#     {"score": 0.880435,
#     "tone_id": "joy",
#     "tone_name": "Joy"},
#     {"score": 0.946222,
#     "tone_id": "tentative",
#     "tone_name": "Tentative"}]}}
def parse_blumix_feedback(feedback):
    feedback = json.loads(str(feedback))
    tones = []
    print("tone_info: {}".format(feedback["document_tone"]["tones"]))
    for tone_info in feedback["document_tone"]["tones"]:
        tones.append([tone_info["tone_id"], tone_info["score"]])
    return tones

def to_str(user_tones):
    tones_str = ""
    if len(user_tones) != 0:
        tones_str = "You sounds "
        for tone in user_tones:
            tones_str = tones_str + tone[0]
    return tones_str