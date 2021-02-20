#!/bin/bash
# vim:et:sta:sts=4:sw=4:ts=8:tw=79:

OPT=$1

export NODES_LIST=${NODES_LIST:-"2 4 6 8 10"}
export BANDWIDTH_LIST=${BANDWIDTH_LIST:-"100Mbps 1000Mbps 10000Mbps"}
export NETWORK_DELAY_LIST=${NETWORK_DELAY_LIST:-"3ms 30ms 60ms"}

# needed for fogify
export MANAGER_NAME="cluster-manager"
export MANAGER_IP=172.17.0.1
export HOST_IP=172.17.0.1 

run_test() {
    docker-compose up --detach
    docker exec -t fogify-db-benchmarks_ui_1 \
        python3 /home/jovyan/work/test-fogify-network/run.py
    docker-compose down
    sleep 30 # give some time for the containers to actually go down
}

for NODES in $NODES_LIST; do
    export NODES
    for BANDWIDTH in $BANDWIDTH_LIST; do
        export BANDWIDTH
        for NETWORK_DELAY in $NETWORK_DELAY_LIST; do
            export NETWORK_DELAY
            # if a file named STOP is present, bail out of doing
            # the rest of the tests. Useful when fogify starts
            # missbehaving.
            if [ -f STOP ]; then
                exit 2
            fi
            # only run test if it hasn't run yet
            combination=$NODES-$BANDWIDTH-$NETWORK_DELAY
            if [ -f output/ping-${combination}-0.out ]; then
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

