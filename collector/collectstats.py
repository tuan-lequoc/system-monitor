#!/usr/bin/python3


import json
import psutil
import os
import collections
import subprocess
import socket
import struct
import time

hostname = socket.gethostname()
prev_io_stats = {}
prev_net_stats = {}

def send_metric(server, port, listdata):
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to Zabbix server
        sock.connect((server, port))

        # Packet header
        header = b'ZBXD\x01'
        data = {
            'request': 'sender data',
            'data': listdata
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
# Function to collect CPU statistics
def collect_cpu_stats():
    cpu_percent = psutil.cpu_percent(interval=1)
    return {'system.cpu.util': cpu_percent}

# Function to collect CPU load
def get_cpu_load_average():
    load_avg_1min, load_avg_5min, load_avg_15min = os.getloadavg()
    return {
        "system.cpu.load[avg1]": load_avg_1min,
        "system.cpu.load[avg5]": load_avg_5min,
        "system.cpu.load[avg15]": load_avg_15min
    }

# Function to collect memory statistics
def collect_memory_stats():
    mem = psutil.virtual_memory()
    cached_ram = mem.total - (mem.used + mem.free)
    return {
        'vm.memory.size[used]': mem.used,
        'vm.memory.size[free]': mem.free,
        'vm.memory.size[cached]': cached_ram
    }

# def collect_disk_stats():
#     disk_stats = {}

#     # Get disk partitions
#     partitions = psutil.disk_partitions(all=False)

#     # Iterate over disk partitions
#     for partition in partitions:
#         if partition.mountpoint.startswith(('/boot', '/snap', '/var')):
#             continue
#         partition_name = partition.mountpoint
#         disk_usage = psutil.disk_usage(partition_name)
#         disk_stats[f'vfs.fs.size[{partition_name},total]'] = disk_usage.total
#         disk_stats[f'vfs.fs.size[{partition_name},used]'] = disk_usage.used
#         disk_stats[f'vfs.fs.size[{partition_name},free]'] = disk_usage.free
#         disk_stats[f'vfs.fs.utilization[{partition_name}]'] = disk_usage.percent
#         # Get disk I/O statistics
#         io_counters = psutil.disk_io_counters(perdisk=True).get(partition.device.split('/')[-1])
#         if io_counters:
#             disk_stats[f'vfs.dev.read_bytes[{partition_name}]'] = io_counters.read_bytes
#             disk_stats[f'vfs.dev.write_bytes[{partition_name}]'] = io_counters.write_bytes

#     return disk_stats

# def collect_network_stats():
#     net_stats = {}
#     for interface, stats in psutil.net_io_counters(pernic=True).items():
#         if interface.startswith(('eth', 'wl')):  # Filter Ethernet and Wireless LAN interfaces
#             net_stats[f'net.if.in[{interface}]'] = stats.bytes_recv
#             net_stats[f'net.if.out[{interface}]'] = stats.bytes_sent
#     return net_stats

def collect_disk_stats():
    global prev_io_stats
    
    disk_stats = {}
    current_time = time.time()

    # Get disk partitions
    partitions = psutil.disk_partitions(all=False)

    # Iterate over disk partitions
    for partition in partitions:
        if partition.mountpoint.startswith(('/boot', '/snap', '/var')):
            continue
        partition_name = partition.mountpoint
        disk_usage = psutil.disk_usage(partition_name)
        disk_stats[f'vfs.fs.size[{partition_name},total]'] = disk_usage.total
        disk_stats[f'vfs.fs.size[{partition_name},used]'] = disk_usage.used
        disk_stats[f'vfs.fs.size[{partition_name},free]'] = disk_usage.free
        disk_stats[f'vfs.fs.utilization[{partition_name}]'] = disk_usage.percent
        # Get disk I/O statistics
        io_counters = psutil.disk_io_counters(perdisk=True).get(partition.device.split('/')[-1])
        if io_counters:
            # Calculate bytes per second for read and write operations
            if partition_name in prev_io_stats:
                prev_read_bytes, prev_write_bytes, prev_time = prev_io_stats[partition_name]
                time_difference = current_time - prev_time
                read_bytes_per_sec = (io_counters.read_bytes - prev_read_bytes) / time_difference
                write_bytes_per_sec = (io_counters.write_bytes - prev_write_bytes) / time_difference
            else:
                read_bytes_per_sec = 0
                write_bytes_per_sec = 0
            
            # Update previous stats
            prev_io_stats[partition_name] = (io_counters.read_bytes, io_counters.write_bytes, current_time)
            
            # Store current stats
            disk_stats[f'vfs.dev.read_bytes[{partition_name}]'] = read_bytes_per_sec
            disk_stats[f'vfs.dev.write_bytes[{partition_name}]'] = write_bytes_per_sec

    return disk_stats

def collect_network_stats():
    global prev_net_stats
    
    net_stats = {}
    current_time = time.time()
    
    for interface, stats in psutil.net_io_counters(pernic=True).items():
        if interface.startswith(('eth', 'wl')):  # Filter Ethernet and Wireless LAN interfaces
            bytes_recv = stats.bytes_recv
            bytes_sent = stats.bytes_sent
            
            # Calculate bytes per second
            if interface in prev_net_stats:
                prev_bytes_recv, prev_bytes_sent, prev_time = prev_net_stats[interface]
                time_difference = current_time - prev_time
                bytes_recv_per_sec = (bytes_recv - prev_bytes_recv) / time_difference
                bytes_sent_per_sec = (bytes_sent - prev_bytes_sent) / time_difference
            else:
                bytes_recv_per_sec = 0
                bytes_sent_per_sec = 0
            
            # Update previous stats
            prev_net_stats[interface] = (bytes_recv, bytes_sent, current_time)
            
            # Store current stats
            net_stats[f'net.if.in[{interface}]'] = bytes_recv_per_sec
            net_stats[f'net.if.out[{interface}]'] = bytes_sent_per_sec
    
    return net_stats

def collect_tcp_stats():
    tcp_stats = collections.defaultdict(int)
    for conn in psutil.net_connections(kind='tcp'):
        status = conn.status
        tcp_stats[f'net.tcp[{status}]'] += 1
    return tcp_stats

def collect_temperature():
    temperature_stats = {}
    try:
        output = subprocess.check_output(['vcgencmd', 'measure_temp'])
        temp_str = output.decode('utf-8').strip()
        temperature = float(temp_str.split('=')[1].split("'")[0])
        temperature_stats['system.cpu.temperature'] = temperature
    except FileNotFoundError:
        print("Error: 'vcgencmd' command not found. Make sure you are running on a Raspberry Pi.")
    except (subprocess.CalledProcessError, IndexError, ValueError) as e:
        print(f"Error occurred while getting CPU temperature: {e}")
    return temperature_stats

# Function to collect all system statistics
def collect_system_stats():
    stats = {}
    stats.update(collect_cpu_stats())
    stats.update(collect_memory_stats())
    stats.update(collect_disk_stats())
    stats.update(get_cpu_load_average())
    stats.update(collect_network_stats())
    stats.update(collect_tcp_stats())
    stats.update(collect_temperature())
    return stats


while True:
    # Collect system statistics
    system_stats = collect_system_stats()

    # Format statistics as Zabbix trap items
    zabbix_trap_items = []
    for key, value in system_stats.items():
        trap_item = {
            "host": hostname,
            "key": key,
            "value": str(value)
        }
        zabbix_trap_items.append(trap_item)

    # # Convert trap items to JSON
    # json_trap_items = json.dumps(zabbix_trap_items, indent=4)

    # # Print JSON string
    # print("Zabbix Trap Items (JSON):")
    # print(json_trap_items)

    send_metric('localhost', 10051, zabbix_trap_items)
    time.sleep(60)
