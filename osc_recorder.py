#!/usr/bin/env python3
"""
OSC Recorder
Records incoming OSC messages to a CSV file.
"""

import csv
import time
import threading
import os
from datetime import datetime
from typing import Optional
from pythonosc import dispatcher, osc_server


class OSCRecorder:
    def __init__(self, listen_ip: str = "127.0.0.1", listen_port: int = 8002, recording_name: str = "agat", status_callback=None):
        """
        Initialize the OSC Recorder.
        
        Args:
            listen_ip: IP address to listen for OSC messages (default: 127.0.0.1)
            listen_port: Port to listen for OSC messages (default: 8002)
            recording_name: Name/prefix for the recording files (default: "agat")
            status_callback: Optional callback function for status messages
        """
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.recording_name = recording_name
        self.status_callback = status_callback
        
        self.is_recording = False
        self.recording_start_time = None
        self.csv_file = None
        self.csv_writer = None
        self.recorded_messages = []
        self.server = None
        self.server_thread = None
        
    def _log(self, message):
        """Log a message using callback or print."""
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)
    
    def _generate_filename(self) -> str:
        """Generate a CSV filename with date and time."""
        timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
        # Sanitize recording name to be filesystem-safe
        safe_name = "".join(c for c in self.recording_name if c.isalnum() or c in ('-', '_')).strip()
        if not safe_name:
            safe_name = "recording"
        return f"{safe_name}_{timestamp}.csv"
    
    def _handle_osc_message(self, address: str, *args):
        """Handle incoming OSC messages."""
        if not self.is_recording:
            return
        
        # Don't record control commands
        if address == "/recordcsv":
            return
        
        # Calculate relative timestamp
        current_time = time.time()
        relative_time = current_time - self.recording_start_time
        
        # Handle arguments - preserve type information
        if len(args) == 0:
            # No arguments - record as empty string
            value = ""
            value_str = ""
        else:
            value = args[0]
            # Convert value to string preserving type information
            if isinstance(value, bool):
                value_str = str(value).lower()
            elif isinstance(value, str):
                value_str = value
            elif isinstance(value, float):
                # Preserve full float precision using repr or higher precision
                value_str = repr(value)  # repr preserves precision better than str
            elif isinstance(value, int):
                value_str = str(value)
            else:
                # Fallback for other types
                value_str = str(value)
        
        # Record the message
        self.recorded_messages.append((relative_time, address, value_str))
        
        # Write to CSV immediately
        if self.csv_writer:
            self.csv_writer.writerow([f"{relative_time:.6f}", address, value_str])
            self.csv_file.flush()  # Ensure data is written immediately
        
        self._log(f"Recorded: {address} = {value_str} ({type(value).__name__}) at {relative_time:.6f}s")
    
    def _handle_recording_control(self, address: str, *args):
        """Handle OSC control commands for recording."""
        if len(args) < 1:
            return
        
        command = args[0]
        
        if address == "/recordcsv":
            if command == 1 or command == 1.0:
                self.start_recording()
            elif command == 0 or command == 0.0:
                self.stop_recording()
    
    def start_recording(self, output_dir: Optional[str] = None):
        """Start recording OSC messages."""
        if self.is_recording:
            self._log("Recording is already in progress")
            return
        
        # Generate filename
        filename = self._generate_filename()
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
        else:
            filepath = filename
        
        try:
            # Open CSV file for writing
            self.csv_file = open(filepath, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csv_file)
            
            # Write header rows
            start_time_str = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
            name_upper = self.recording_name.upper()
            self.csv_file.write(f"# {name_upper} OSC Recording\n")
            self.csv_file.write(f"# Started: {start_time_str}\n")
            self.csv_file.write(f"# Format: timestamp,address,value\n")
            self.csv_file.write(f"time,address,value\n")
            self.csv_file.flush()
            
            # Initialize recording
            self.recording_start_time = time.time()
            self.is_recording = True
            self.recorded_messages = []
            
            self._log(f"Recording started: {filepath}")
            
            # Ensure OSC server is running
            if not self.server:
                self.start_server()
                
        except Exception as e:
            self._log(f"Error starting recording: {e}")
            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None
                self.csv_writer = None
            raise
    
    def stop_recording(self):
        """Stop recording OSC messages."""
        if not self.is_recording:
            self._log("Recording is not in progress")
            return
        
        self.is_recording = False
        
        if self.csv_file:
            # Calculate duration
            if self.recording_start_time:
                duration = time.time() - self.recording_start_time
                self.csv_file.write(f"\n# Duration: {duration:.1f} seconds\n")
            
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
            
            self._log(f"Recording stopped. Recorded {len(self.recorded_messages)} messages")
        
        self.recording_start_time = None
    
    def start_server(self):
        """Start the OSC server to listen for messages."""
        if self.server:
            return
        
        def run_server():
            disp = dispatcher.Dispatcher()
            
            # Map all OSC addresses to the message handler
            disp.map("/*", self._handle_osc_message)
            
            # Map control commands
            disp.map("/recordcsv", self._handle_recording_control)
            
            try:
                self.server = osc_server.ThreadingOSCUDPServer(
                    (self.listen_ip, self.listen_port), disp
                )
                self._log(f"OSC recorder server started on {self.listen_ip}:{self.listen_port}")
                self._log("Send /recordcsv 1 to start, /recordcsv 0 to stop")
                self.server.serve_forever()
            except OSError as e:
                if e.errno == 48:  # Address already in use
                    self._log(f"Warning: Port {self.listen_port} is already in use")
                else:
                    self._log(f"Error starting OSC server: {e}")
            except Exception as e:
                self._log(f"OSC server error: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
    
    def stop_server(self):
        """Stop the OSC server."""
        if self.server:
            self.server.shutdown()
            self.server = None
            self._log("OSC recorder server stopped")
    
    def get_recording_filepath(self) -> Optional[str]:
        """Get the filepath of the current recording file."""
        if self.csv_file:
            return self.csv_file.name
        return None

