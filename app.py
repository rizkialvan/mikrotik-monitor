#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MikroTik Monitoring Dashboard
Real-time health & interface utilization
"""

import os
from flask import Flask, render_template, jsonify
from librouteros import connect
from librouteros.exceptions import LibRouterosError, ConnectionClosed
import threading
import time

app = Flask(__name__)

# MikroTik Configuration from environment
MIKROTIK_CONFIG = {
    'host': os.getenv('MIKROTIK_HOST', '103.133.56.21'),
    'port': int(os.getenv('MIKROTIK_PORT', '53000')),
    'username': os.getenv('MIKROTIK_USER', 'jose'),
    'password': os.getenv('MIKROTIK_PASSWORD', 'josejose'),
    'plaintext_login': True,
}

# Cache for data
data_cache = {
    'system': None,
    'interfaces': None,
    'last_update': None,
    'error': None,
}

def fetch_mikrotik_data():
    """Fetch data from MikroTik"""
    try:
        routeros = connect(**MIKROTIK_CONFIG)
        
        # System resource
        system_data = {}
        for item in routeros.path('/system/resource'):
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
        interfaces_data = []
        for iface in routeros.path('/interface'):
            interfaces_data.append({
                'name': iface.get('name', 'unknown'),
                'type': iface.get('type', 'unknown'),
                'running': iface.get('running', False),
                'tx_byte': iface.get('tx-byte', 0),
                'rx_byte': iface.get('rx-byte', 0),
            })
        
        # Get interface stats (traffic)
        for stat in routeros.path('/interface/monitor-traffic'):
            name = stat.get('name')
            for iface in interfaces_data:
                if iface['name'] == name:
                    iface['tx_rate'] = stat.get('tx-rate', 0)
                    iface['rx_rate'] = stat.get('rx-rate', 0)
                    # Calculate total rate in Mbps
                    total_rate = int(iface.get('tx_rate', 0)) + int(iface.get('rx_rate', 0))
                    iface['total_rate_mbps'] = round(total_rate / 1_000_000, 2)
                    break
        
        routeros.close()
        
        # Update cache
        data_cache['system'] = system_data
        data_cache['interfaces'] = interfaces_data
        data_cache['last_update'] = time.time()
        data_cache['error'] = None
        
        return True
        
    except Exception as e:
        data_cache['error'] = str(e)
        return False

# Background refresh
def background_refresh():
    while True:
        fetch_mikrotik_data()
        time.sleep(5)  # Refresh every 5 seconds

# Start background thread
refresh_thread = threading.Thread(target=background_refresh, daemon=True)
refresh_thread.start()

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
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': time.time()})

if __name__ == '__main__':
    # Initial fetch
    fetch_mikrotik_data()
    
    # Run Flask
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
