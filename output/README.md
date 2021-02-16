# About this directory

The test output files will be placed in here once the YCSB tests are
completed. The file names follow the pattern:
```
DB-WORKLOAD-NODES-REPLICAS-BANDWIDTH-NETWORK_DELAY-OP_COUNT-REC_COUNT-THREAD_COUNT-ACTION-REPLICATION
```

where:
* `DB`: the database that was tested
* `WORKLOAD`: the YCSB workload used
* `NODES`: the total number of database nodes
* `REPLICAS`: the number of slave nodes per master node
* `BANDWIDTH`: the bandwidth allocated between nodes
* `NETWORK_DELAY`: the network delay between nodes
* `OP_COUNT`: the YCSB test operation count
* `REC_COUNT`: the YCSB test record count
* `THREAD_COUNT`: the YCSB test thread count
* `ACTION`: the YCSB test action (load/run)
* `REPLICATION`: the replication number of the test

