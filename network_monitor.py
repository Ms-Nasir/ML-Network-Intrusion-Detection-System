import os
import time
import json
import pandas as pd
import threading
import queue
import socket
import struct
import platform
from datetime import datetime
from collections import defaultdict, deque
from scapy.all import sniff, IP, TCP, UDP, ICMP, conf

# Import the machine learning model
from model import NIDSModel

class NetworkMonitor:
    def __init__(self, interface=None, model_path='model/nids_model.pkl'):
        self.interface = interface
        self.packet_queue = queue.Queue()
        self.stop_flag = threading.Event()
        self.connection_stats = defaultdict(lambda: defaultdict(int))
        self.recent_alerts = deque(maxlen=50)
        self.alert_listeners = []
        self.stats_listeners = []
        
        # Time window for statistics (in seconds)
        self.time_window = 5
        self.last_stats_reset = time.time()
        
        # Load the ML model
        self.model = NIDSModel(model_path)
        try:
            self.model.load_model()
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Will attempt to train a new model")
            
        # Start threads
        self.processing_thread = threading.Thread(target=self._process_packets)
        self.stats_thread = threading.Thread(target=self._generate_stats)
        self.processing_thread.daemon = True
        self.stats_thread.daemon = True
    
    def start(self):
        """Start the network monitoring"""
        if not self.processing_thread.is_alive():
            self.stop_flag.clear()
            self.processing_thread.start()
            self.stats_thread.start()
            print(f"Network monitoring started on interface: {self.interface or 'default'}")
            
            # Start packet capture
            self._start_capture()
    
    def stop(self):
        """Stop the network monitoring"""
        self.stop_flag.set()
        if self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
        if self.stats_thread.is_alive():
            self.stats_thread.join(timeout=2.0)
        print("Network monitoring stopped")
    
    def add_alert_listener(self, callback):
        """Add a callback function to receive alerts"""
        self.alert_listeners.append(callback)
    
    def add_stats_listener(self, callback):
        """Add a callback function to receive statistics updates"""
        self.stats_listeners.append(callback)
    
    def get_recent_alerts(self):
        """Get the most recent alerts"""
        return list(self.recent_alerts)
    
    def _start_capture(self):
        """Start capturing packets using Scapy"""
        try:
            # Always use None for interface to ensure default is used when needed
            # This is a simple fix that should work on all platforms
            use_interface = None
            if self.interface and self.interface != "Default":
                use_interface = self.interface
                
            print(f"Starting packet capture with interface: {use_interface or 'Default system interface'}")
            
            # Start a new thread for sniffing to avoid blocking
            sniff_thread = threading.Thread(
                target=lambda: sniff(
                    iface=use_interface,  # None will use default interface
                    prn=self._packet_callback,
                    store=0,
                    stop_filter=lambda x: self.stop_flag.is_set()
                )
            )
            sniff_thread.daemon = True
            sniff_thread.start()
            print("Packet capture started successfully!")
        except Exception as e:
            print(f"Error starting packet capture: {e}")
            raise  # Re-raise the exception to be handled by the caller
    
    def _packet_callback(self, packet):
        """Callback for each captured packet"""
        try:
            if IP in packet:
                parsed_packet = self._parse_packet(packet)
                self.packet_queue.put(parsed_packet)
                # Print basic packet info to confirm packets are being captured
                src = packet[IP].src
                dst = packet[IP].dst
                proto_str = "TCP" if TCP in packet else "UDP" if UDP in packet else "ICMP" if ICMP in packet else "Other"
                print(f"Captured packet: {src} -> {dst} [{proto_str}]")
        except Exception as e:
            print(f"Error processing packet: {e}")
    
    def _parse_packet(self, packet):
        """Parse a packet into features for our model"""
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst
        proto = None
        sport = 0
        dport = 0
        flags = ''
        
        # Determine protocol
        if TCP in packet:
            proto = 'tcp'
            sport = packet[TCP].sport
            dport = packet[TCP].dport
            flags = self._parse_tcp_flags(packet[TCP].flags)
        elif UDP in packet:
            proto = 'udp'
            sport = packet[UDP].sport
            dport = packet[UDP].dport
            flags = 'SF'  # Assuming all UDP packets are SF (normal flow)
        elif ICMP in packet:
            proto = 'icmp'
            flags = 'SF'  # Assuming all ICMP packets are SF
        else:
            proto = 'other'
            flags = 'OTH'  # Other protocol
        
        # Determine service based on port number
        service = self._get_service_name(dport, proto)
        
        # Extract basic metrics
        pkt_size = len(packet)
        timestamp = datetime.now().timestamp()
        
        # Generate connection key
        conn_key = f"{ip_src}:{sport}-{ip_dst}:{dport}-{proto}"
        
        # Update connection statistics
        self.connection_stats[conn_key]['count'] += 1
        self.connection_stats[conn_key]['bytes'] += pkt_size
        self.connection_stats[conn_key]['last_seen'] = timestamp
        
        # Get more advanced features based on our dataset requirements
        # These would typically be calculated over time windows
        # For now, we'll set placeholder values
        features = {
            'duration': 0,  # Will be calculated later based on connection
            'protocol_type': proto,
            'service': service,
            'flag': flags,
            'src_bytes': pkt_size if ip_src != '127.0.0.1' else 0,
            'dst_bytes': 0,  # Will be updated as we see return traffic
            'land': 1 if ip_src == ip_dst else 0,
            'wrong_fragment': 0,  # Would need deeper inspection
            'urgent': 0,  # Would need TCP flags analysis
            'hot': 0,  # Application-level feature, can't determine from raw packets
            'num_failed_logins': 0,  # Application-level feature
            'logged_in': 0,  # Application-level feature
            'num_compromised': 0,  # Application-level feature
            'root_shell': 0,  # Application-level feature
            'su_attempted': 0,  # Application-level feature
            'num_root': 0,  # Application-level feature
            'num_file_creations': 0,  # Application-level feature
            'num_shells': 0,  # Application-level feature
            'num_access_files': 0,  # Application-level feature
            'num_outbound_cmds': 0,  # Application-level feature
            'is_host_login': 0,  # Application-level feature
            'is_guest_login': 0,  # Application-level feature
            'count': self.connection_stats[conn_key]['count'],
            'srv_count': sum(1 for k in self.connection_stats if k.split('-')[2] == proto and 
                           k.split('-')[1].split(':')[1] == str(dport)),
            'serror_rate': 0.0,  # Would need connection tracking
            'srv_serror_rate': 0.0,  # Would need connection tracking
            'rerror_rate': 0.0,  # Would need connection tracking
            'srv_rerror_rate': 0.0,  # Would need connection tracking
            'same_srv_rate': 1.0,  # Simplified for real-time
            'diff_srv_rate': 0.0,  # Simplified for real-time
            'srv_diff_host_rate': 0.0,  # Simplified for real-time
            'dst_host_count': 1,  # Simplified for real-time
            'dst_host_srv_count': 1,  # Simplified for real-time
            'dst_host_same_srv_rate': 1.0,  # Simplified for real-time
            'dst_host_diff_srv_rate': 0.0,  # Simplified for real-time
            'dst_host_same_src_port_rate': 1.0,  # Simplified for real-time
            'dst_host_srv_diff_host_rate': 0.0,  # Simplified for real-time
            'dst_host_serror_rate': 0.0,  # Would need connection tracking
            'dst_host_srv_serror_rate': 0.0,  # Would need connection tracking
            'dst_host_rerror_rate': 0.0,  # Would need connection tracking
            'dst_host_srv_rerror_rate': 0.0  # Would need connection tracking
        }
        
        # Add metadata for tracking and display
        metadata = {
            'timestamp': timestamp,
            'src_ip': ip_src,
            'src_port': sport,
            'dst_ip': ip_dst,
            'dst_port': dport,
            'protocol': proto,
            'packet_size': pkt_size,
            'connection_key': conn_key
        }
        
        return {'features': features, 'metadata': metadata}
    
    def _process_packets(self):
        """Process packets from the queue and detect anomalies"""
        while not self.stop_flag.is_set():
            try:
                if not self.packet_queue.empty():
                    packet_data = self.packet_queue.get(timeout=1.0)
                    
                    # Analyze the packet using the ML model
                    result = self.model.predict(packet_data['features'])
                    
                    # If it's an attack with high probability, generate an alert
                    if result['is_attack'] and result['probability'] > 0.7:
                        alert = {
                            'timestamp': datetime.now().isoformat(),
                            'src_ip': packet_data['metadata']['src_ip'],
                            'src_port': packet_data['metadata']['src_port'],
                            'dst_ip': packet_data['metadata']['dst_ip'],
                            'dst_port': packet_data['metadata']['dst_port'],
                            'protocol': packet_data['metadata']['protocol'],
                            'probability': result['probability'],
                            'connection_key': packet_data['metadata']['connection_key']
                        }
                        
                        self.recent_alerts.append(alert)
                        
                        # Notify listeners
                        for listener in self.alert_listeners:
                            try:
                                listener(alert)
                            except Exception as e:
                                print(f"Error in alert listener: {e}")
                else:
                    time.sleep(0.1)  # Sleep briefly if queue is empty
            except queue.Empty:
                pass  # Queue timeout, continue
            except Exception as e:
                print(f"Error processing packet: {e}")
                time.sleep(0.5)  # Sleep to avoid tight loop on error
    
    def _generate_stats(self):
        """Generate network statistics periodically"""
        while not self.stop_flag.is_set():
            try:
                # Check if it's time to generate stats
                current_time = time.time()
                if current_time - self.last_stats_reset >= self.time_window:
                    # Calculate statistics
                    stats = {
                        'timestamp': datetime.now().isoformat(),
                        'total_connections': len(self.connection_stats),
                        'active_connections': sum(1 for k, v in self.connection_stats.items() 
                                           if current_time - v['last_seen'] < self.time_window),
                        'total_packets': sum(v['count'] for v in self.connection_stats.values()),
                        'total_bytes': sum(v['bytes'] for v in self.connection_stats.values()),
                        'protocols': {
                            'tcp': sum(1 for k in self.connection_stats if k.split('-')[2] == 'tcp'),
                            'udp': sum(1 for k in self.connection_stats if k.split('-')[2] == 'udp'),
                            'icmp': sum(1 for k in self.connection_stats if k.split('-')[2] == 'icmp'),
                            'other': sum(1 for k in self.connection_stats if k.split('-')[2] == 'other')
                        },
                        'alerts_count': len(self.recent_alerts)
                    }
                    
                    # Notify listeners
                    for listener in self.stats_listeners:
                        try:
                            listener(stats)
                        except Exception as e:
                            print(f"Error in stats listener: {e}")
                    
                    # Clean up old connections
                    self._cleanup_connections(current_time)
                    
                    # Update last reset time
                    self.last_stats_reset = current_time
                
                time.sleep(1.0)  # Check every second
            except Exception as e:
                print(f"Error generating stats: {e}")
                time.sleep(1.0)
    
    def _cleanup_connections(self, current_time):
        """Remove old connections from tracking"""
        # Keep connections for a longer period (30 seconds)
        timeout = 30.0
        keys_to_remove = []
        
        for key, data in self.connection_stats.items():
            if current_time - data['last_seen'] > timeout:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.connection_stats[key]
    
    def _parse_tcp_flags(self, flags):
        """Convert TCP flags to string representation"""
        flag_map = {
            'F': 'FIN',
            'S': 'SYN',
            'R': 'RST',
            'P': 'PUSH',
            'A': 'ACK',
            'U': 'URG'
        }
        
        # Common flag combinations in our dataset
        if flags & 0x02 and flags & 0x10:  # SYN-ACK
            return 'S1'
        elif flags & 0x02:  # SYN
            return 'S0'
        elif flags & 0x01 and flags & 0x10:  # FIN-ACK
            return 'SF'
        elif flags & 0x04:  # RST
            return 'REJ'
        else:
            return 'OTH'  # Other flag combinations
    
    def _get_service_name(self, port, proto):
        """Map port numbers to service names"""
        common_ports = {
            21: 'ftp',
            22: 'ssh',
            23: 'telnet',
            25: 'smtp',
            53: 'domain',
            80: 'http',
            110: 'pop3',
            123: 'ntp',
            143: 'imap',
            443: 'https',
            445: 'microsoft-ds',
            993: 'imaps',
            995: 'pop3s',
            3306: 'mysql',
            3389: 'ms-wbt-server',
            8080: 'http-proxy'
        }
        
        if port in common_ports:
            return common_ports[port]
        elif port < 1024:
            return 'other'
        else:
            return 'private'

def get_network_interfaces():
    """Get available network interfaces"""
    if platform.system() == "Windows":
        # On Windows, just return the simplest option
        return ["Default"]
    else:
        # On Linux/Mac, use available interfaces from os
        return os.listdir('/sys/class/net') if os.path.exists('/sys/class/net') else ["Default"]