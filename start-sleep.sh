#!/bin/bash
# vim:et:sta:sts=4:sw=4:ts=8:tw=79:

# needed for fogify
export MANAGER_NAME="cluster-manager"
export MANAGER_IP=172.17.0.1
export HOST_IP=172.17.0.1 

run_test() {
    docker-compose up --detach
    docker exec -t fogify-db-benchmarks_ui_1 \
        python3 /home/jovyan/work/test-sleep/run.py
    docker-compose down
    sleep 30 # give some time for the containers to actually go down
}

run_test

