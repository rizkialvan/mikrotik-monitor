#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MikroTik Monitoring Dashboard - REST API Version
Real-time health & interface utilization
"""

import os
import sys
import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from flask import Flask, render_template, jsonify
import threading
import time

# Disable SSL warning (self-signed certs)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)

# MikroTik REST API Configuration
MIKROTIK_CONFIG = {
    'host': os.getenv('MIKROTIK_HOST', '103.133.56.21'),
    'port': int(os.getenv('MIKROTIK_PORT_REST', '443')),  # REST API port (443 or 80)
    'username': os.getenv('MIKROTIK_USER', 'jose'),
    'password': os.getenv('MIKROTIK_PASSWORD', 'josejose'),
    'protocol': os.getenv('MIKROTIK_PROTOCOL', 'https'),  # https or http
    'timeout': 10,
}

# Build base URL
BASE_URL = f"{MIKROTIK_CONFIG['protocol']}://{MIKROTIK_CONFIG['host']}:{MIKROTIK_CONFIG['port']}"

# Cache for data
data_cache = {
    'system': None,
    'interfaces': None,
    'last_update': None,
    'error': None,
    'fetch_count': 0,
}

def fetch_mikrotik_data():
    """Fetch data from MikroTik REST API"""
    try:
        auth = HTTPBasicAuth(MIKROTIK_CONFIG['username'], MIKROTIK_CONFIG['password'])
        
        # System resource
        sys_url = f"{BASE_URL}/rest/system/resource"
        sys_resp = requests.get(sys_url, auth=auth, timeout=MIKROTIK_CONFIG['timeout'], verify=False)
        sys_resp.raise_for_status()
        sys_data = sys_resp.json()
        
        system_data = {}
        if sys_data and len(sys_data) > 0:
            item = sys_data[0]
            system_data = {
                'uptime': item.get('uptime', 'N/A'),
                'cpu_load': item.get('cpu-load', '0'),
                'free_memory': item.get('free-memory', '0'),
                'total_memory': item.get('total-memory', '0'),
                'version': item.get('version', 'N/A'),
            }
            
            # Calculate memory usage
            if system_data.get('free_memory') and system_data.get('total_memory'):
                free = int(system_data['free_memory'])
                total = int(system_data['total_memory'])
                used = total - free
                system_data['memory_used'] = used
                system_data['memory_percent'] = round((used / total) * 100, 2) if total > 0 else 0
        
        # Interfaces
        iface_url = f"{BASE_URL}/rest/interface"
        iface_resp = requests.get(iface_url, auth=auth, timeout=MIKROTIK_CONFIG['timeout'], verify=False)
        iface_resp.raise_for_status()
        iface_data = iface_resp.json()
        
        interfaces_data = []
        for iface in iface_data:
            interfaces_data.append({
                'name': iface.get('name', 'unknown'),
                'type': iface.get('type', 'unknown'),
                'running': iface.get('running', False),
                'tx_byte': iface.get('tx-byte', 0),
                'rx_byte': iface.get('rx-byte', 0),
            })
        
        # Get interface stats (traffic) - separate endpoint
        traffic_url = f"{BASE_URL}/rest/interface/monitor-traffic"
        traffic_resp = requests.post(traffic_url, auth=auth, timeout=MIKROTIK_CONFIG['timeout'], verify=False)
        if traffic_resp.status_code == 200:
            traffic_data = traffic_resp.json()
            for stat in traffic_data:
                name = stat.get('name')
                for iface in interfaces_data:
                    if iface['name'] == name:
                        iface['tx_rate'] = stat.get('tx-rate', 0)
                        iface['rx_rate'] = stat.get('rx-rate', 0)
                        # Calculate total rate in Mbps
                        total_rate = int(iface.get('tx_rate', 0)) + int(iface.get('rx_rate', 0))
                        iface['total_rate_mbps'] = round(total_rate / 1_000_000, 2)
                        break
        
        # Update cache
        data_cache['system'] = system_data
        data_cache['interfaces'] = interfaces_data
        data_cache['last_update'] = time.time()
        data_cache['error'] = None
        data_cache['fetch_count'] = data_cache.get('fetch_count', 0) + 1
        
        print(f"✅ Fetch success: {len(interfaces_data)} interfaces", file=sys.stderr)
        return True
        
    except requests.exceptions.Timeout:
        error_msg = f"Connection timeout: {BASE_URL}"
        data_cache['error'] = error_msg
        data_cache['fetch_count'] = data_cache.get('fetch_count', 0) + 1
        print(f"❌ Timeout: {error_msg}", file=sys.stderr)
        return False
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        data_cache['error'] = error_msg
        data_cache['fetch_count'] = data_cache.get('fetch_count', 0) + 1
        print(f"❌ Connection: {error_msg}", file=sys.stderr)
        return False
        
    except Exception as e:
        error_msg = f"API error: {str(e)}"
        data_cache['error'] = error_msg
        data_cache['fetch_count'] = data_cache.get('fetch_count', 0) + 1
        print(f"❌ Error: {error_msg}", file=sys.stderr)
        return False

# Background refresh
def background_refresh():
    while True:
        fetch_mikrotik_data()
        time.sleep(5)  # Refresh every 5 seconds

# Start background thread
refresh_thread = threading.Thread(target=background_refresh, daemon=True)
refresh_thread.start()

# Initial fetch (run immediately)
print(f"🔄 Starting REST API fetch from {BASE_URL}...", file=sys.stderr)
fetch_mikrotik_data()
print(f"📊 Initial fetch: {data_cache['fetch_count']} attempts, error={data_cache['error']}", file=sys.stderr)

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """API endpoint for dashboard data"""
    return jsonify({
        'success': data_cache['error'] is None,
        'system': data_cache['system'],
        'interfaces': data_cache['interfaces'],
        'last_update': data_cache['last_update'],
        'error': data_cache['error'],
        'fetch_count': data_cache.get('fetch_count', 0),
        'base_url': BASE_URL,
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': time.time()})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
