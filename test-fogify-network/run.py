#!/usr/bin/env python3
# vim:et:sta:sts=4:sw=4:ts=8:tw=79:

import os
import sys
import time
import socket
import subprocess
from FogifySDK import FogifySDK

settings = {}
settings['nodes'] = int(os.environ['NODES'])
settings['bandwidth'] = os.environ['BANDWIDTH']
settings['network_delay'] = os.environ['NETWORK_DELAY']

def valid_ip(ip):
    try:
        socket.inet_aton(ip)
    except socket.error:
        return False
    return True

def check_containers(container_ip):
    for ip in container_ip:
        if valid_ip(ip):
            print(f"DB container (IP: {ip}) is confirmed running.")
        else:
            raise Exception(f"DB container (IP: {ip}) is not running.")

def install_iperf3(container_id, container_ip):
    for cid in container_id:
        cmd = f"sudo docker exec {cid} apk update"
        p = subprocess.getstatusoutput(cmd)
        print(p[1])
        cmd = f"sudo docker exec {cid} apk add iperf3"
        p = subprocess.getstatusoutput(cmd)
        print(p[1])

def iperf3_run(container_id, container_ip):
    iperf_processes = []
    for i in range(len(container_ip)):
        if i % 2 == 0:
            cmd = f"sudo docker exec {container_id[i]} iperf3 -s -D"
        else:
            cmd = f"sudo docker exec {container_id[i]} iperf3 -c {container_ip[i-1]}"
        p = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        iperf_processes.append(p)
    time.sleep(30)
    for i in range(len(iperf_processes)):
        if i %2 != 0:
            output, err = iperf_processes[i].communicate()
            fname = f"/home/jovyan/work/output/iperf3-{settings['nodes']}-{settings['bandwidth']}-{settings['network_delay']}-{i}.out"
            with open(fname, 'w') as f:
                f.write(output.decode())
    ping_processes = []
    for i in range(len(container_ip)):
        if i % 2 == 0:
            cmd = f"sudo docker exec {container_id[i]} ping -c 10 {container_ip[i-1]}"
            p = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ping_processes.append(p)
    time.sleep(20)
    for i in range(len(ping_processes)):
            output, err = ping_processes[i].communicate()
            fname = f"/home/jovyan/work/output/ping-{settings['nodes']}-{settings['bandwidth']}-{settings['network_delay']}-{i}.out"
            with open(fname, 'w') as f:
                f.write(output.decode())

# create fogify-setup.yaml file for this run
with open('/home/jovyan/work/test-fogify-network/fogify-setup-template.yaml', 'r') as f:
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
    # allow for 2 sec/node to spin up, but no more that 2 mins. It should be
    # enough, even for 100 nodes
    wait_time = 2 * settings['nodes']
    if wait_time > 120:
        wait_time = 120
    time.sleep(wait_time)
    info = fogify.info()
    container_id = []
    container_ip = []
    for i in range(settings['nodes']):
        cid = info['fogify_node'][i]['Status']['ContainerStatus']['ContainerID']
        cip = info["fogify_node"][i]['NetworksAttachments'][0]['Addresses'][0].rpartition('/')[0]
        container_id.append(cid)
        container_ip.append(cip)
    check_containers(container_ip)
    install_iperf3(container_id, container_ip)
    time.sleep(5)
    iperf3_run(container_id, container_ip)
    time.sleep(120)
finally:
    try:
        print("Undeploying...")
        fogify.undeploy()
    except:
        pass

