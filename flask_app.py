from flask import Flask, request, abort
import git
import json
import os
import requests
app = Flask(__name__)

wa_secret = os.getenv("wa_secret")

@app.route('/update_server', methods=['POST'])
def webhook():
    if request.method != 'POST':
        return 'OK'
    else:
        abort_code = 418
        # Do initial validations on required headers
        if 'X-Github-Event' not in request.headers:
            print("abort")
            abort(abort_code)
        if 'X-Github-Delivery' not in request.headers:
            print("abort")
            abort(abort_code)
        if 'X-Hub-Signature' not in request.headers:
            print("abort")
            abort(abort_code)
        if not request.is_json:
            print("abort")
            abort(abort_code)
        if 'User-Agent' not in request.headers:
            print("abort")
            abort(abort_code)
        ua = request.headers.get('User-Agent')
        if not ua.startswith('GitHub-Hookshot/'):
            print("abort")
            abort(abort_code)

        event = request.headers.get('X-GitHub-Event')
        if event == "ping":
            return json.dumps({'msg': 'Hi!'})
        if event != "push":
            return json.dumps({'msg': "Wrong event type"})

        x_hub_signature = request.headers.get('X-Hub-Signature')
        # webhook content type should be application/json for request.data to have the payload
        # request.data is empty in case of x-www-form-urlencoded
        if not is_valid_signature(x_hub_signature, request.data, w_secret):
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

@app.route('/github/release', methods=['GET'])
def return_github_release():
    return get_shields_endpoint("Github latest release", get_github_release_api("name"))

@app.route('/snap/beta', methods=['GET']):
def return_snap_beta():
    return get_shields_endpoint("Snapcraft beta channel", get_snapcraft_channel_version("beta"))

@app.route('/snap/edge', methods=['GET']):
def return_snap_beta():
    return get_shields_endpoint("Snapcraft edge channel", get_snapcraft_channel_version("edge"))

def get_shields_endpoint(label,message,color='blue'):
    schema = {
        "schemaVersion": 1,
        "label": label,
        "message": message,
        "color": color
    }
    return json.dumps(schema)

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
    
def get_snapcraft_info_api(key):
    url = "https://api.snapcraft.io/v2/snaps/info/fortius-ant"
    headers = {
        "User-Agent": "My User Agent 1.0",
        "Snap-Device-Series": "16",
    }
    try:
        response = requests.get(url, headers=headers, timeout=0.1)
        responseDict = json.loads(response.text)
        return responseDict[key]
    except requests.exceptions.RequestException:
        return "No response"
    
def get_snapcraft_channel_info(channel):
    snapcraft_channel_map = get_snapcraft_info_api("channel")
    for i in range(0,len(snapcraft_channel_map)-1):
        if snapcraft_channel_map[i]["name"] == channel:
            index = i
            break
    if index:
        return snapcraft_channel_map[i]
    else:
        return "No channel matching this name"

def get_snapcraft_channel_version(channel):
    channel_info = get_snapcraft_channel_info(channel)
    return channel_info["version"]
