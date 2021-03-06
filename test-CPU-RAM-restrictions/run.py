#!/usr/bin/env python3
# vim:et:sta:sts=4:sw=4:ts=8:tw=79:

import os
import sys
import time
import socket
import subprocess
from FogifySDK import FogifySDK

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

time.sleep(5) # wait a bit before deploying again
try:
    fogify = FogifySDK("http://controller:5000",
            "/home/jovyan/work/test-CPU-RAM-restrictions/fogify-setup.yaml")
    res = fogify.deploy()
    print(res)
    wait_time = 10
    time.sleep(wait_time)
    info = fogify.info()
    container_id = []
    container_ip = []
    cid = info['fogify_node'][0]['Status']['ContainerStatus']['ContainerID']
    cip = info["fogify_node"][0]['NetworksAttachments'][0]['Addresses'][0].rpartition('/')[0]
    container_id.append(cid)
    container_ip.append(cip)
    check_containers(container_ip)
    time.sleep(30)
finally:
    try:
        print("Undeploying...")
        fogify.undeploy()
    except:
        pass

