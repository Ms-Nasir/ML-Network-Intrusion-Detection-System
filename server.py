import os
import json
import time
import threading
import argparse
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from model import NIDSModel
from network_monitor import NetworkMonitor, get_network_interfaces

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'nids-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Create directories if they don't exist
os.makedirs('data', exist_ok=True)
os.makedirs('model', exist_ok=True)
os.makedirs('static', exist_ok=True)

# Global variables
monitor = None
dataset_path = 'data/nids_data.csv'
model_path = 'model/nids_model.pkl'
data_loaded = False

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    # Send current stats on connect
    if monitor:
        emit('stats_update', {'status': 'running' if monitor else 'stopped'})
        emit('alerts', {'alerts': monitor.get_recent_alerts()})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Flask routes
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/interfaces')
def get_interfaces():
    interfaces = get_network_interfaces()
    return jsonify({'interfaces': interfaces})

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    global monitor
    
    data = request.json
    interface = data.get('interface', None)
    
    # Don't use "Default Interface" string directly
    if interface == "Default" or interface == "Default Interface":
        interface = None
    
    if monitor is None:
        # Initialize and start the monitor
        monitor = NetworkMonitor(interface=interface, model_path=model_path)
        
        # Add event listeners
        monitor.add_alert_listener(alert_callback)
        monitor.add_stats_listener(stats_callback)
        
        try:
            # Start monitoring
            monitor.start()
            return jsonify({'status': 'started', 'interface': interface or 'default'})
        except Exception as e:
            monitor = None
            return jsonify({'status': 'error', 'message': str(e)})
    else:
        return jsonify({'status': 'already_running'})

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    global monitor
    
    if monitor:
        monitor.stop()
        monitor = None
        return jsonify({'status': 'stopped'})
    else:
        return jsonify({'status': 'not_running'})

@app.route('/api/status')
def get_status():
    if monitor:
        return jsonify({'status': 'running'})
    else:
        return jsonify({'status': 'stopped'})

@app.route('/api/alerts')
def get_alerts():
    if monitor:
        return jsonify({'alerts': monitor.get_recent_alerts()})
    else:
        return jsonify({'alerts': []})

@app.route('/api/load_dataset', methods=['POST'])
def load_dataset():
    global data_loaded
    
    try:
        if os.path.exists(dataset_path):
            # Save uploaded data to file
            with open(dataset_path, 'w') as f:
                f.write(request.data.decode('utf-8'))
            data_loaded = True
            return jsonify({'status': 'success', 'message': 'Dataset loaded successfully'})
        else:
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
            
            # Save uploaded data to file
            with open(dataset_path, 'w') as f:
                f.write(request.data.decode('utf-8'))
            data_loaded = True
            return jsonify({'status': 'success', 'message': 'Dataset created successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/train_model', methods=['POST'])
def train_model():
    if not data_loaded and not os.path.exists(dataset_path):
        return jsonify({'status': 'error', 'message': 'No dataset available for training'})
    
    try:
        # Train the model in a separate thread
        def train():
            model = NIDSModel(model_path)
            model.train_model(dataset_path)
            socketio.emit('model_trained', {'status': 'success'})
        
        threading.Thread(target=train).start()
        return jsonify({'status': 'training', 'message': 'Model training started in background'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Callback functions
def alert_callback(alert):
    """Callback for new alerts"""
    socketio.emit('new_alert', alert)

def stats_callback(stats):
    """Callback for statistics updates"""
    socketio.emit('stats_update', stats)

def init_app():
    """Initialize the application"""
    global data_loaded
    
    # Check if dataset exists
    if os.path.exists(dataset_path):
        data_loaded = True
    
    # Check if model exists, if not and data exists, train the model
    if not os.path.exists(model_path) and data_loaded:
        model = NIDSModel(model_path)
        model.train_model(dataset_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Network Intrusion Detection System')
    parser.add_argument('--host', default='0.0.0.0', help='Host address to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Initialize the application
    init_app()
    
    # Run the server
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)