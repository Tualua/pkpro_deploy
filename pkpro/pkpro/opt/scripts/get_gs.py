#!/usr/bin/python
import requests
import xml.etree.ElementTree as ET

PK_DEVAPI = "http://apidev.playkey.net/update.aspx?software=GameServer"
response = requests.get(PK_DEVAPI)
xml = response.text
root = ET.fromstring(xml)
version = root.find('version').text
url = root.find('url').text
filename = root.find('files').find('file').find('filename').text
link = "{}/GameServer/{}/{}".format(url, version, filename)
print(link)
