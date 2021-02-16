#!/bin/bash
# vim:et:sta:sts=4:sw=4:ts=8:tw=79:

export REPLICATIONS=${REPLICATIONS:-5}
export REPLICAS=${REPLICAS:-4}
export YCSB_THREAD_COUNT=${YCSB_THREAD_COUNT:-4}
export NODES_LIST=${NODES_LIST:-"50 35 25 15"}
export BANDWIDTH_LIST=${BANDWIDTH_LIST:-"1000Mbps 500Mbps"}
export NETWORK_DELAY_LIST=${NETWORK_DELAY_LIST:-"70ms"}
export YCSB_OPERATION_COUNT_LIST=${YCSB_OPERATION_COUNT_LIST:-"1000000 500000 100000"}
export YCSB_RECORD_COUNT_LIST=${YCSB_RECORD_COUNT_LIST:-"1000000 500000 100000"}

# needed for fogify
export MANAGER_NAME="cluster-manager"
export MANAGER_IP=172.17.0.1
export HOST_IP=172.17.0.1 

run_test() {
    echo "*********************"
    echo "*** TEST SETTINGS ***"
    echo "*********************"
    echo "Replications: $REPLICATIONS"
    echo "Number of nodes: $NODES"
    echo "Number of replicas: $REPLICAS"
    echo "Network bandwidth: $BANDWIDTH"
    echo "Network delay: $NETWORK_DELAY"
    echo "YCSB operationcount: $YCSB_OPERATION_COUNT"
    echo "YCSB recordcount: $YCSB_RECORD_COUNT"
    echo "YCSB threadcount: $YCSB_THREAD_COUNT"

    for REPLICATION in `seq $REPLICATIONS`; do
        export REPLICATION
        docker-compose up --detach
        docker exec -t fogify-db-benchmarks_ui_1 \
            python3 /home/jovyan/work/redis-cluster/run.py
        docker-compose down
        sleep 10 # give some time for the containers to actually go down
    done
}

for NODES in $NODES_LIST; do
    export NODES
    for BANDWIDTH in $BANDWIDTH_LIST; do
        export BANDWIDTH
        for NETWORK_DELAY in $NETWORK_DELAY_LIST; do
            export NETWORK_DELAY
            for YCSB_OPERATION_COUNT in $YCSB_OPERATION_COUNT_LIST; do
                export YCSB_OPERATION_COUNT
                for YCSB_RECORD_COUNT in $YCSB_RECORD_COUNT_LIST; do
                    export YCSB_RECORD_COUNT
                    run_test
                done
            done
        done
    done
done

