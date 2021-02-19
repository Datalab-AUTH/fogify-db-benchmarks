#!/bin/bash
# vim:et:sta:sts=4:sw=4:ts=8:tw=79:

OPT=$1

export REPLICATIONS=${REPLICATIONS:-1}
export REPLICAS=${REPLICAS:-1}
export YCSB_THREAD_COUNT=${YCSB_THREAD_COUNT:-4}
export NODES_LIST=${NODES_LIST:-"100 50 30 20 15"}
export BANDWIDTH_LIST=${BANDWIDTH_LIST:-"1000Mbps"}
export NETWORK_DELAY_LIST=${NETWORK_DELAY_LIST:-"3ms"}
export YCSB_OPERATION_COUNT_LIST=${YCSB_OPERATION_COUNT_LIST:-"1000 5000 10000 20000"}
export YCSB_RECORD_COUNT_LIST=${YCSB_RECORD_COUNT_LIST:-"1000 5000 10000 20000"}

# needed for fogify
export MANAGER_NAME="cluster-manager"
export MANAGER_IP=172.17.0.1
export HOST_IP=172.17.0.1 

run_test() {
    echo "*********************"
    echo "*** TEST SETTINGS ***"
    echo "*********************"
    echo "Replication: $REPLICATION/$REPLICATIONS"
    echo "Number of nodes: $NODES"
    echo "Number of replicas: $REPLICAS"
    echo "Network bandwidth: $BANDWIDTH"
    echo "Network delay: $NETWORK_DELAY"
    echo "YCSB operationcount: $YCSB_OPERATION_COUNT"
    echo "YCSB recordcount: $YCSB_RECORD_COUNT"
    echo "YCSB threadcount: $YCSB_THREAD_COUNT"

    docker-compose up --detach
    docker exec -t fogify-db-benchmarks_ui_1 \
        python3 /home/jovyan/work/redis-cluster/run.py
    docker-compose down
    sleep 30 # give some time for the containers to actually go down
}

for REPLICATION in `seq $REPLICATIONS`; do
    export REPLICATION
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
                        # if a file named STOP is present, bail out of doing
                        # the rest of the tests. Useful when fogify starts
                        # missbehaving.
                        if [ -f STOP ]; then
                            exit 2
                        fi
                        # only run test if it hasn't run yet
                        combination=$NODES-$REPLICAS-$BANDWIDTH
                        combination=$combination-$NETWORK_DELAY
                        combination=$combination-$YCSB_OPERATION_COUNT
                        combination=$combination-$YCSB_RECORD_COUNT
                        combination=$combination-$YCSB_THREAD_COUNT
                        combination=$combination-run-$REPLICATION
                        if [ -f output/redis-f-$combination.out ]; then
                            echo "*** $combination already there. Skipping. ***"
                        else
                            if [[ $OPT == "-s" ]]; then
                                echo "*** $combination will be run ***"
                            else
                                run_test
                            fi
                        fi
                    done
                done
            done
        done
    done
done

