#!/bin/sh

MANAGER_NAME="cluster-manager" \
	MANAGER_IP=172.17.0.1 \
	HOST_IP=172.17.0.1 \
	docker-compose up
docker-compose down
