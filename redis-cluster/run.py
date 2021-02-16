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
settings['replicas'] = int(os.environ['REPLICAS'])
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

def redis_cluster_create(container_ip):
    redis_cluster_create_cmd = f"sudo docker exec {first_container_id} /usr/local/bin/redis-cli --cluster create"
    for i in range(settings['nodes']):
        redis_cluster_create_cmd += f" {container_ip[i]}:6379"
    if settings['replicas'] > 0:
        redis_cluster_create_cmd += f" --cluster-replicas {settings['replicas']}"
    redis_cluster_create_cmd += ' --cluster-yes'
    print(redis_cluster_create_cmd)
    p = subprocess.getstatusoutput(redis_cluster_create_cmd)
    print(p[1])
    if p[0] != 0:
        raise Exception("Could not create redis cluster")

def redis_ycsb_run(ycsb_id, host_ip):
    for workload in ['a', 'b', 'c', 'd', 'e', 'f']:
        for action in ['load', 'run']:
            cmd = "sudo docker exec {}".format(ycsb_id)
            cmd += " ./bin/ycsb {} redis".format(action)
            cmd += " -s -P ./workloads/workload{}".format(workload)
            cmd += " -p 'redis.host={}'".format(host_ip)
            cmd += " -p 'redis.port=6379'"
            cmd += " -p 'operationcount={}'".format(settings['ycsb_operation_count'])
            cmd += " -p 'recordcount={}'".format(settings['ycsb_record_count'])
            cmd += " -p 'threadcount={}'".format(settings['ycsb_thread_count'])
            cmd += " -p 'redis.cluster=true'"
            print(cmd)
            p = subprocess.getstatusoutput(cmd)
            print(p[1])
            if p[0] != 0:
                print("ERROR: Test failed.")
                print(settings)
            else:
                fname = f"/home/jovyan/work/output/redis-{workload}"
                fname += f"-{settings['nodes']}"
                fname += f"-{settings['replicas']}"
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
with open('/home/jovyan/work/redis-cluster/fogify-setup-template.yaml', 'r') as f:
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
    time.sleep(10)
    info = fogify.info()
    ycsb_container_id = info['fogify_ycsb'][0]['Status']['ContainerStatus']['ContainerID']
    ycsb_container_ip = info["fogify_ycsb"][0]['NetworksAttachments'][0]['Addresses'][0].rpartition('/')[0]
    first_container_id = info['fogify_node'][0]['Status']['ContainerStatus']['ContainerID']
    container_ip = []
    for i in range(settings['nodes']):
        ip = info["fogify_node"][i]['NetworksAttachments'][0]['Addresses'][0].rpartition('/')[0]
        container_ip.append(ip)
    check_containers(ycsb_container_ip, container_ip)
    redis_cluster_create(container_ip)
    redis_ycsb_run(ycsb_container_id, container_ip[0])
finally:
    try:
        print("Undeploying...")
        fogify.undeploy()
    except:
        pass

