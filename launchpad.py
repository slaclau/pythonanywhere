from flask import Blueprint

import requests

from flask_app import get_shields_endpoint

launchpad = Blueprint('launchpad', __name__)

@launchpad.route("/launchpad/<ppa>")
def return_launchpad_ppa_api(ppa):
    return get_launchpad_ppa_api(ppa)
    
@launchpad.route("/launchpad/<ppa>/<source>/build")
def return_launchpad_build_records(ppa,source):
    return get_launchpad_ppa_build_records(ppa,source)
    
@launchpad.route("/launchpad/<ppa>/<source>/binary")
def return_launchpad_build_records(ppa,source):
    return get_launchpad_ppa_binaries(ppa,source)
    
@launchpad.route("/launchpad/<ppa>/<source>/binary/<distribution>/version")
def return_launchpad_binary_version(ppa,source, distribution):
    version =  get_launchpad_ppa_binary_version(ppa,source,distribution)
    return get_shields_endpoint("Version",version)
    
def get_launchpad_ppa_api(ppa,operation=None,distribution=None,query=None,key=None):
    url = "https://api.launchpad.net/devel/~slaclau/+archive/ubuntu/" + ppa
    if operation != None:
        url = url + "?ws.op=" + operation
    if distribution !=None:
        url = url + "&distro_arch_series=https://api.launchpad.net/devel/ubuntu/" + distribution + "/amd64"
    if query != None:
        url = url + "&" + query 
    try:
        response = json.loads(requests.get(url, timeout=0.5).text)
        if key == None:
            return response
        else:
            return response[key]
    except requests.exceptions.RequestException:
        return "No response"
    

def get_launchpad_ppa_build_records(ppa,source,distribution=None,key=None):
    return get_launchpad_ppa_api(ppa,operation="getBuildRecords", distribution=distribution, query="source_name=" + source,key=key)

def get_launchpad_ppa_binaries(ppa,source,distribution=None,index=None,key=None):
    rtn = get_launchpad_ppa_api(ppa,operation="getPublishedBinaries",  distribution=distribution, query="binary_name=" + source,key="entries")
    if index != None:
        rtn = rtn[index]
        if key != None:
            return rtn[key]
    elif len(rtn) == 1:
        rtn = rtn[0]
        if key != None:
            return rtn[key]
    else:
        return rtn

def get_launchpad_ppa_binary_version(ppa,source,distribution):
    return get_launchpad_ppa_binaries(ppa, source, distribution, index=0,key="binary_package_version")


