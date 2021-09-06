#!/usr/bin/python

import xml.etree.ElementTree as ET, json

def get_servers(path="/usr/local/etc/gameserver/conf.xml"):
    tree = ET.parse(path)
    root = tree.getroot()
    vms = []
    for server in root.iter('Server'):
        print(server.get('name'))

get_servers()
