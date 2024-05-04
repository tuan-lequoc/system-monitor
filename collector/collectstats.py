#!/usr/bin/python3


import struct
import socket
import json

def send_metric(server, port, hostname, key, value):
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to Zabbix server
        sock.connect((server, port))

        # Packet header
        header = b'ZBXD\x01'
        data = {
            'request': 'sender data',
            'data': [{
                'host': hostname,
                'key': key,
                'value': str(value)
            }]
        }

        # Convert data to JSON
        data_json = json.dumps(data).encode('utf-8')

        # Pack header and JSON data
        packet = header + struct.pack('<Q', len(data_json)) + data_json

        # Send packet
        sock.sendall(packet)

        # Receive response
        response_header = sock.recv(5)
        if response_header != b'ZBXD\x01':
            print("Invalid response received from Zabbix server")
            return

        response_data_len = sock.recv(8)
        response_data_len = struct.unpack('<Q', response_data_len)[0]
        response_data = sock.recv(response_data_len)
        response = json.loads(response_data.decode('utf-8'))

        # Check response
        if response.get('response') == 'success':
            print("Metric sent successfully")
        else:
            print("Failed to send metric")
    finally:
        # Close socket
        sock.close()

############################# get metrics ###############################
import psutil

def get_cpu_load():
    # Get CPU load
    cpu_load = psutil.cpu_percent(interval=1)  # Interval is in seconds, adjust as needed
    return cpu_load


# Example usage
send_metric('localhost', 10051, 'tuanle-service', 'system.cpu.load', get_cpu_load())