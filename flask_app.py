from flask import Flask, request, abort
import git
import hmac
import hashlib
import json
import os
import requests

from launchpad import launchpad
from utils import get_shields_endpoint

app = Flask(__name__)
app.register_blueprint(launchpad)

wa_secret = os.getenv("wa_secret")

@app.route('/update_server', methods=['POST'])
def webhook():
    if request.method != 'POST':
        return 'OK'
    else:
        abort_code = 418
        # Do initial validations on required headers
        if 'X-Github-Event' not in request.headers:
            abort(abort_code)
        if 'X-Github-Delivery' not in request.headers:
            abort(abort_code)
        if 'X-Hub-Signature' not in request.headers:
            abort(abort_code)
        if not request.is_json:
            abort(abort_code)
        if 'User-Agent' not in request.headers:
            abort(abort_code)
        ua = request.headers.get('User-Agent')
        if not ua.startswith('GitHub-Hookshot/'):
            abort(abort_code)
        event = request.headers.get('X-GitHub-Event')
        if event == "ping":
            return json.dumps({'msg': 'Hi!'})
        if event != "push":
            return json.dumps({'msg': "Wrong event type"})

        x_hub_signature = request.headers.get('X-Hub-Signature')
        # webhook content type should be application/json for request.data to have the payload
        # request.data is empty in case of x-www-form-urlencoded
        if not is_valid_signature(x_hub_signature, request.data, wa_secret):
            print('Deploy signature failed: {sig}'.format(sig=x_hub_signature))
            abort(abort_code)

        payload = request.get_json()
        if payload is None:
            print('Deploy payload is empty: {payload}'.format(
                payload=payload))
            abort(abort_code)

        if payload['ref'] != 'refs/heads/master':
            return json.dumps({'msg': 'Not master; ignoring'})

        repo = git.Repo('/home/slaclau/mysite')
        origin = repo.remotes.origin

        pull_info = origin.pull()

        if len(pull_info) == 0:
            return json.dumps({'msg': "Didn't pull any information from remote!"})
        if pull_info[0].flags > 128:
            return json.dumps({'msg': "Didn't pull any information from remote!"})

        commit_hash = pull_info[0].commit.hexsha
        build_commit = f'build_commit = "{commit_hash}"'
        print(f'{build_commit}')
        return 'Updated PythonAnywhere server to commit {commit}'.format(commit=commit_hash)

def is_valid_signature(x_hub_signature, data, private_key):
    # x_hub_signature and data are from the webhook payload
    # private key is your webhook secret
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)

@app.route('/github/release', methods=['GET'])
def return_github_release():
    return get_shields_endpoint("Github latest release", get_github_release_api("name"))

@app.route('/snap', methods=['GET'])
def return_snap_api():
    return get_snapcraft_info_api()

@app.route('/snap/beta', methods=['GET'])
def return_snap_beta():
    return get_shields_endpoint("Snapcraft beta channel", get_snapcraft_channel_version("beta"))

@app.route('/snap/edge', methods=['GET'])
def return_snap_edge():
    return get_shields_endpoint("Snapcraft edge channel", get_snapcraft_channel_version("edge"))

def get_github_release_api(key):
    url = "https://api.github.com/repos/slaclau/FortiusANT/releases/latest"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        response = requests.get(url, headers=headers, timeout=0.1)
        responseDict = json.loads(response.text)
        return responseDict[key]
    except requests.exceptions.RequestException:
        return "No response"
    
def get_snapcraft_info_api(key=None):
    url = "https://api.snapcraft.io/v2/snaps/info/fortius-ant"
    headers = {
        "User-Agent": "My User Agent 1.0",
        "Snap-Device-Series": "16",
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        responseDict = json.loads(response.text)
        if key == None:
            return responseDict
        else:
            return responseDict[key]
    except requests.exceptions.RequestException:
        return "No response"
    
def get_snapcraft_channel_info(channel):
    snapcraft_channel_map = get_snapcraft_info_api("channel-map")
    for i in range(0,len(snapcraft_channel_map)):
        if snapcraft_channel_map[i]["channel"]["name"] == channel:
            index = i
            break
    try:
        return snapcraft_channel_map[index]
    except NameError:
        return "No channel matching this name"

def get_snapcraft_channel_version(channel):
    channel_info = get_snapcraft_channel_info(channel)
    return channel_info["version"]