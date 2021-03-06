#!/usr/bin/python -u
import select
import sys
from systemd import journal
from prometheus_client import start_http_server, Gauge, Info
from pyzabbix import ZabbixMetric, ZabbixSender
import xml.etree.ElementTree as ET
from platform import node


def get_zabbix_conf(path='/etc/zabbix/zabbix_agentd.conf'):
    try:
        zbx_conf = open(path, 'r')
    except Exception:
        print('Failed to open Zabbix Agent config!')
        sys.exit(1)
    else:
        agent_hostname = None
        for line in zbx_conf.readlines():
            if 'Server=' in line and '#' not in line:
                servers = line.split('=')[-1].split(',')
            elif 'Hostname=' in line and '#' not in line:
                agent_hostname = line.split('=')[-1].replace('\n', '')
        if '127.0.0.1' in servers:
            servers.remove('127.0.0.1')
    if not agent_hostname:
        agent_hostname = node()

    zabbix_server = servers[0].replace('\n', '')
    zbx_conf.close()
    return zabbix_server, agent_hostname


# Read VM names from GameServer config
def get_servers(path="/usr/local/etc/gameserver/conf.xml"):
    tree = ET.parse(path)
    root = tree.getroot()
    vms = []
    for server in root.iter('Server'):
        vms.append(server.get('name'))
    return vms


zabbix_server, agent_hostname = get_zabbix_conf()
exclude_processes = ['EpicGamesLauncher.exe']

vms = get_servers()
session = {}
j = journal.Reader()
j.log_level(journal.LOG_INFO)
j.add_match(
    _SYSTEMD_UNIT=u'gameserver.service')

j.seek_tail()
j.get_previous()
p = select.poll()
p.register(j, j.get_events())

gauge_fps_present = Gauge('fps_present', 'FPS rendered by game', ['vm'])
gauge_fps_customer = Gauge('fps_customer', 'FPS got by customer', ['vm'])
gauge_latency = Gauge('latency', 'Customer latency', ['vm'])
zbx_metrics = []
fps_present, fps_customer, latency = 0, 0, 0
info_session = Info('session', 'GameServer Session Data', ['vm'])
start_http_server(8000)
zbx = ZabbixSender(zabbix_server)

for vm in vms:
    session[vm] = {'id': '', 'game': '', 'active': True}
    info_session.labels(vm=vm).info({'id': session[vm]['id'], 'game': session[vm]['id']})
    gauge_fps_customer.labels(vm=vm).set(0)
    gauge_fps_present.labels(vm=vm).set(0)
    gauge_latency.labels(vm=vm).set(0)

while p.poll():
    if j.process() != journal.APPEND:
        continue
    for entry in j:
        log_message = entry['MESSAGE']
        if log_message != "":
            zbx_metrics = []
            vm = entry['SYSLOG_IDENTIFIER'].split('/')[-1]
            if ' CreateSession: session_id' in log_message:
                session[vm]['id'] = log_message.split(' = ')[-1].split(' ')[-1]
                session[vm]['active'] = True
                info_session.labels(vm=vm).info({'id': session[vm]['id'], 'game': session[vm]['id']})
                gauge_fps_customer.labels(vm=vm).set(0)
                gauge_fps_present.labels(vm=vm).set(0)
                gauge_latency.labels(vm=vm).set(0)
                print("Session started at {}: {}".format(vm, session[vm]['id']))
                zbx_session_id = ZabbixMetric(agent_hostname, 'playkey.gs.session.id[{}]'.format(vm), session[vm]['id'])
                try:
                    zbx.send([zbx_session_id])
                except Exception:
                    print('Failed to send metrics to Zabbix Server!')
                    pass
            elif '<GAME_CODE>' in log_message:
                session[vm]['game'] = log_message.split('<GAME_CODE>')[-1].split('<')[0]
                info_session.labels(vm=vm).info({'id': session[vm]['id'], 'game': session[vm]['game']})
                print("VM: {} ID: {} G: {} GF: {} CF: {} L: {}".format(vm, session[vm]['id'], session[vm]['game'],
                                                                       fps_present, fps_customer, latency))
                zbx_session_game = ZabbixMetric(agent_hostname, 'playkey.gs.session.game[{}]'.format(vm),
                                                session[vm]['game'])
                try:
                    zbx.send([zbx_session_game])
                except Exception:
                    print('Failed to send metrics to Zabbix Server!')
                    pass
            elif 'FPS (for last 5 sec)' in log_message and session[vm]['active']:
                fps_customer = int(log_message.split(' U: ')[1].split(' ')[0])
                gauge_fps_customer.labels(vm=vm).set(fps_customer)
                print("VM: {} ID: {} G: {} GF: {} CF: {} L: {}".format(vm, session[vm]['id'], session[vm]['game'],
                                                                       fps_present, fps_customer, latency))
                zbx_fps_customer = ZabbixMetric(agent_hostname, 'playkey.gs.fps.customer[{}]'.format(vm), fps_customer)
                try:
                    zbx.send([zbx_fps_customer])
                except Exception:
                    print('Failed to send metrics to Zabbix Server!')
                    pass
            elif 'Present (FPS' in log_message and session[vm]['active']:
                process = log_message.split(': ')[1]
                if process not in exclude_processes:
                    fps_present = int(log_message.split('FPS = ')[1].split(')')[0])
                    gauge_fps_present.labels(vm=vm).set(fps_present)
                    print("VM: {} ID: {} G: {} GF: {} CF: {} L: {}".format(vm, session[vm]['id'], session[vm]['game'],
                                                                           fps_present, fps_customer, latency))
                    zbx_fps_present = ZabbixMetric(agent_hostname, 'playkey.gs.fps.present[{}]'.format(vm), fps_present)
                    try:
                        zbx.send([zbx_fps_present])
                    except Exception:
                        print('Failed to send metrics to Zabbix Server!')
                        pass
            elif 'Check session: session_id' in log_message and session[vm]['active']:
                session[vm]['id'] = log_message.split(' ')[-1]
                print("VM: {} ID: {} G: {} GF: {} CF: {} L: {}".format(vm, session[vm]['id'], session[vm]['game'],
                                                                       fps_present, fps_customer, latency))
                info_session.labels(vm=vm).info({'id': session[vm]['id'], 'game': session[vm]['game']})
                zbx_session_id = ZabbixMetric(agent_hostname, 'playkey.gs.session.id[{}]'.format(vm), session[vm]['id'])
                try:
                    zbx.send([zbx_session_id])
                except Exception:
                    print('Failed to send metrics to Zabbix Server!')
                    pass
            elif 'Ping (for last 5 sec)' in log_message and session[vm]['active']:
                latency = int(log_message.split(': ')[-1].split(' ')[0])
                gauge_latency.labels(vm=vm).set(latency)
                print("VM: {} ID: {} G: {} GF: {} CF: {} L: {}".format(vm, session[vm]['id'], session[vm]['game'],
                                                                       fps_present, fps_customer, latency))
                zbx_latency = ZabbixMetric(agent_hostname, 'playkey.gs.latency[{}]'.format(vm), latency)
                try:
                    zbx.send([zbx_latency])
                except Exception:
                    print('Failed to send metrics to Zabbix Server!')
                    pass
            elif 'OnCloseClient' in log_message:
                print("VM: {} ID: {} G: {} GF: {} CF: {} L: {}".format(vm, session[vm]['id'], session[vm]['game'],
                                                                       fps_present, fps_customer, latency))
                print("Session finished at {}: {}".format(vm, session[vm]['id']))
                session[vm] = {'id': '', 'game': ''}
                session[vm]['active'] = False
                fps_present, fps_customer, latency = 0, 0, 0
                info_session.labels(vm=vm).info({'id': session[vm]['id'], 'game': session[vm]['game']})
                gauge_fps_customer.labels(vm=vm).set(0)
                gauge_fps_present.labels(vm=vm).set(0)
                gauge_latency.labels(vm=vm).set(0)
                zbx_session_id = ZabbixMetric(agent_hostname, 'playkey.gs.session.id[{}]'.format(vm), session[vm]['id'])
                zbx_session_game = ZabbixMetric(agent_hostname, 'playkey.gs.session.game[{}]'.format(vm),
                                                session[vm]['game'])
                zbx_fps_customer = ZabbixMetric(agent_hostname, 'playkey.gs.fps.customer[{}]'.format(vm), fps_customer)
                zbx_fps_present = ZabbixMetric(agent_hostname, 'playkey.gs.fps.present[{}]'.format(vm), fps_present)
                zbx_latency = ZabbixMetric(agent_hostname, 'playkey.gs.latency[{}]'.format(vm), latency)
                try:
                    zbx.send([zbx_session_id, zbx_session_game, zbx_fps_customer, zbx_fps_present, zbx_latency])
                except Exception:
                    print('Failed to send metrics to Zabbix Server!')
                    pass
