#!/usr/bin/env python3
# vim:et:sta:sts=4:sw=4:ts=8:tw=79:

import os
import sys
import time
import socket
import subprocess
from FogifySDK import FogifySDK

settings = {}
settings['variant'] = os.environ['VARIANT']
settings['nodes'] = int(os.environ['NODES'])
settings['bandwidth'] = os.environ['BANDWIDTH']
settings['network_delay'] = os.environ['NETWORK_DELAY']
settings['ycsb_operation_count'] = int(os.environ['YCSB_OPERATION_COUNT'])
settings['ycsb_record_count'] = int(os.environ['YCSB_RECORD_COUNT'])
settings['ycsb_thread_count'] = int(os.environ['YCSB_THREAD_COUNT'])
settings['replication'] = int(os.environ['REPLICATION'])

def valid_ip(ip):
    try:
        socket.inet_aton(ip)
    except socket.error:
        return False
    return True

def check_containers(ycsb_container_ip, container_ip):
    if valid_ip(ycsb_container_ip):
        print(f"YCSB container (IP: {ycsb_container_ip}) is confirmed running.")
    else:
        raise Exception(f"YCSB container (IP: {ycsb_container_ip}) is not running.")
    for ip in container_ip:
        if valid_ip(ip):
            print(f"DB container (IP: {ip}) is confirmed running.")
        else:
            raise Exception(f"DB container (IP: {ip}) is not running.")

def ignite_cluster_create(container_id, container_ip):
    ip_xml_list = ""
    for ip in container_ip:
        ip_xml_list = ip_xml_list + f"<value>{ip}</value>"
    for cid in container_id:
        sed_cmd = f"sudo docker exec {cid}"
        sed_cmd += f" sed -i 's|<!--IP_LIST-->|{ip_xml_list}|' /{settings['variant']}.xml"
        subprocess.getstatusoutput(sed_cmd)
        cp_cmd = f"sudo docker exec {cid}"
        cp_cmd += f" cp /{settings['variant']}.xml config/default-config.xml"
        subprocess.getstatusoutput(cp_cmd)
    for cid in container_id:
        run_cmd = f"sudo docker exec {cid}"
        run_cmd += f" ./run.sh"
        subprocess.Popen(run_cmd.split(' '))
        time.sleep(5 * 60) # wait for ignite to load before starting another instance

def ignite_ycsb_run(ycsb_id, host_ip):
    for workload in ['a', 'b', 'c', 'd', 'e', 'f']:
        for action in ['load', 'run']:
            cmd = "sudo docker exec {}".format(ycsb_id)
            cmd += " ./bin/ycsb {}".format(action)
            cmd += " {}".format(settings['variant'])
            cmd += " -s -P ./workloads/workload{}".format(workload)
            cmd += " -p 'hosts={}'".format(host_ip)
            cmd += " -p 'operationcount={}'".format(settings['ycsb_operation_count'])
            cmd += " -p 'recordcount={}'".format(settings['ycsb_record_count'])
            cmd += " -p 'threadcount={}'".format(settings['ycsb_thread_count'])
            print(cmd)
            p = subprocess.getstatusoutput(cmd)
            print(p[1])
            if p[0] != 0:
                print("ERROR: Test failed.")
                print(settings)
            else:
                fname = f"/home/jovyan/work/output/{settings['variant']}-{workload}"
                fname += f"-{settings['nodes']}"
                fname += f"-{settings['bandwidth']}"
                fname += f"-{settings['network_delay']}"
                fname += f"-{settings['ycsb_operation_count']}"
                fname += f"-{settings['ycsb_record_count']}"
                fname += f"-{settings['ycsb_thread_count']}"
                fname += f"-{action}"
                fname += f"-{settings['replication']}.out"
                with open(fname, 'w') as f:
                    f.write(p[1])

# create fogify-setup.yaml file for this run
with open('/home/jovyan/work/ignite/fogify-setup-template.yaml', 'r') as f:
    with open('fogify-setup.yaml', 'w') as fw:
        for l in f.readlines():
            fw.write(l.replace('__BANDWIDTH__',
                settings['bandwidth']).replace('__NETWORK_DELAY__',
                    settings['network_delay']).replace('__REPLICAS__',
                        str(settings['nodes'])))

time.sleep(5) # wait a bit before deploying again
try:
    fogify = FogifySDK("http://controller:5000", "fogify-setup.yaml")
    res = fogify.deploy()
    print(res)
    # allow for 2 sec/node to spin up, but no more that 2 mins.
    wait_time = 2 * settings['nodes']
    if wait_time > 120:
        wait_time = 120
    print(f"Waiting for {wait_time} seconds...")
    time.sleep(wait_time)
    info = fogify.info()
    ycsb_container_id = info['fogify_ycsb'][0]['Status']['ContainerStatus']['ContainerID']
    ycsb_container_ip = info["fogify_ycsb"][0]['NetworksAttachments'][0]['Addresses'][0].rpartition('/')[0]
    container_id = []
    container_ip = []
    for i in range(settings['nodes']):
        cid = info['fogify_node'][i]['Status']['ContainerStatus']['ContainerID']
        cip = info["fogify_node"][i]['NetworksAttachments'][0]['Addresses'][0].rpartition('/')[0]
        container_id.append(cid)
        container_ip.append(cip)
    check_containers(ycsb_container_ip, container_ip)
    ignite_cluster_create(container_id, container_ip)
    ignite_ycsb_run(ycsb_container_id, container_ip[0])
finally:
    try:
        print("Undeploying...")
        fogify.undeploy()
    except:
        pass

