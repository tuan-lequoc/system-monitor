#!/usr/bin/python3

import json
import psutil
import socket
import struct

def send_llds(server, port, lld_data):
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to Zabbix server
        sock.connect((server, port))

        # Packet header
        header = b'ZBXD\x01'
        data = {
            'request': 'sender data',
            'data': lld_data
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
            print("LLD sent successfully")
        else:
            print("Failed to send LLD")
    finally:
        # Close socket
        sock.close()

#################### collect #######################
hostname = socket.gethostname()
def get_network_interface_names():
    interfaces = psutil.net_if_addrs()
    filtered_interfaces = []

    for interface_name in interfaces.keys():
        if interface_name.startswith(('eth', 'wl', "en")):
            filtered_interfaces.append({"{#IFNAME}": interface_name})

    return filtered_interfaces


def get_all_lld():
    llds = []
    llds.append({"net.if.discovery": get_network_interface_names()})
    return llds

def generate_lld_payload(llds):
    payload = []
    
    for lld in llds:
        for key, value in lld.items():
            payload.append({
                "host": hostname,
                "key": key,
                "value": json.dumps(value)
            })
    
    return payload

llds = get_all_lld()
payload = generate_lld_payload(llds)
print(payload)

# send_llds('localhost', 10051, payload)
