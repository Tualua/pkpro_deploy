#!/usr/bin/python

import xml.etree.ElementTree as ET
import json


def get_servers(path="/usr/local/etc/gameserver/conf.xml"):
    tree = ET.parse(path)
    root = tree.getroot()
    vms = []
    for server in root.iter('Server'):
        vms.append([server.get('name'), server.find('IP').text])
    return vms


vmsinfo = []
# vmsinfo["lld"] = []

defined_servers = get_servers()
if defined_servers:
    for server in defined_servers:
        vmsinfo.append({'vmname': server[0], 'vmip': server[1]})

print(json.dumps(vmsinfo, sort_keys=True, indent=4))
