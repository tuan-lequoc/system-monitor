#!/bin/bash

# Set etcd endpoints and credentials if necessary
ETCD_ENDPOINTS="http://localhost:2379"  # Replace with your etcd endpoint

# Function to get value from etcd
get_etcd_value() {
  local key=$1
  etcdctl --endpoints=$ETCD_ENDPOINTS get "$key" --print-value-only
}

USERNAME=$(get_etcd_value "/config/influxdb-monitor-data/username")
PASSWORD=$(get_etcd_value "/config/influxdb-monitor-data/password")
GRAFANA_CRT=$(get_etcd_value "/config/grafana/grafana.crt")
GRAFANA_KEY=$(get_etcd_value "/config/grafana/grafana.key")

sed -i "s/username: \".*\"/username: \"$USERNAME\"/" otel-collector-config.yml
sed -i "s/password: \".*\"/password: \"$PASSWORD\"/" otel-collector-config.yml

sudo cp -f "$GRAFANA_CRT" certs/grafana.crt
sudo cp -f "$GRAFANA_KEY" certs/grafana.key

sudo chown -R `whoami`:`whoami` certs
