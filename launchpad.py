from flask import Blueprint

launchpad = Blueprint('launchpad', __main__)

@launchpad.route("/launchpad/<ppa>")
def return_launchpad_ppa_api(ppa):
    return get_launchpad_ppa_api(ppa)
    
@launchpad.route("/launchpad/<ppa>/<source>")
def return_launchpad_build_records(ppa,source):
    return get_launchpad_ppa_build_records(ppa,source)
    
def get_launchpad_ppa_api(ppa,request=None,key=None):
    url = "https://api.launchpad.net/devel/~slaclau/+archive/ubuntu/" + ppa
    if request != None:
        url = url + request
    try:
        response = requests.get(url, timeout=0.1)
        responseDict = json.loads(response.text)
        if key == None:
            return responseDict
        else:
            return responseDict[key]
    except requests.exceptions.RequestException:
        return "No response"
    

def get_launchpad_ppa_build_records(ppa,source,key=None):
    return get_launchpad_ppa_api(ppa,request="ws.op=getBuildRecords&source_name=" + source,key=key)

