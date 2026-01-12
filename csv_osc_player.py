#!/usr/bin/env python3
"""
CSV OSC Player
Reads a CSV file and sends OSC messages according to timestamps.
CSV format: timestamp, osc_address, value
"""

import csv
import time
import threading
import argparse
import re
from typing import List, Tuple, Union
from pythonosc import osc_server
from pythonosc import dispatcher
from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder


class CSVOSCPlayer:
    def __init__(self, csv_file: str, osc_ip: str, osc_port: int, control_port: int = 8000, status_callback=None):
        """
        Initialize the CSV OSC Player.
        
        Args:
            csv_file: Path to the CSV file
            osc_ip: Destination IP address for OSC messages
            osc_port: Destination port for OSC messages
            control_port: Port to listen for control commands (default: 8000)
            status_callback: Optional callback function for status messages (takes message string)
        """
        self.csv_file = csv_file
        self.osc_client = udp_client.SimpleUDPClient(osc_ip, osc_port)
        self.osc_ip = osc_ip
        self.osc_port = osc_port
        self.control_port = control_port
        self.status_callback = status_callback
        
        self.events: List[Tuple[float, str, Union[int, float]]] = []
        self.playback_thread: threading.Thread = None
        self.is_playing = False
        self.start_time = None
    
    def _log(self, message):
        """Log a message using callback or print."""
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)
        
    def load_csv(self):
        """Load and parse the CSV file."""
        self.events = []
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row_num, row in enumerate(reader, 1):
                    # Skip the first 4 rows
                    if row_num <= 4:
                        continue
                    
                    if len(row) < 3:
                        self._log(f"Warning: Row {row_num} has fewer than 3 columns, skipping")
                        continue
                    
                    try:
                        timestamp = float(row[0].strip())
                        osc_address = row[1].strip()
                        value_str = row[2].strip()
                        
                        # Handle empty values
                        if not value_str:
                            value = None
                        # Handle boolean values (True/False, true/false)
                        elif value_str.lower() == 'true':
                            value = True
                        elif value_str.lower() == 'false':
                            value = False
                        # Try to parse as number - but be careful with strings that look like numbers
                        else:
                            # Check if it's a valid numeric string (allows digits, decimal point, e/E, +/-, whitespace)
                            numeric_pattern = re.compile(r'^[\s]*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?[\s]*$')
                            
                            if numeric_pattern.match(value_str):
                                # It's numeric - parse it
                                try:
                                    # Try integer first (if no decimal point or 'e')
                                    if '.' not in value_str and 'e' not in value_str.lower() and 'E' not in value_str:
                                        value = int(float(value_str))  # Parse as float first to handle "1.0", then convert
                                    else:
                                        value = float(value_str)
                                except (ValueError, OverflowError):
                                    # Parse failed - treat as string
                                    value = value_str
                            else:
                                # Contains non-numeric characters - treat as string
                                value = value_str
                        
                        self.events.append((timestamp, osc_address, value))
                        
                    except ValueError as e:
                        self._log(f"Warning: Could not parse row {row_num}: {e}")
                        continue
            
            if not self.events:
                raise ValueError("No valid events found in CSV file")
            
            self._log(f"Loaded {len(self.events)} events from {self.csv_file}")
            
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {self.csv_file}")
        except Exception as e:
            raise Exception(f"Error loading CSV file: {e}")
    
    def _playback_loop(self):
        """Internal method to handle playback timing."""
        if not self.events:
            self._log("No events to play")
            return
        
        # Sort events by timestamp (just in case)
        sorted_events = sorted(self.events, key=lambda x: x[0])
        
        # Get the first timestamp as the baseline
        first_timestamp = sorted_events[0][0]
        
        # Calculate relative times
        relative_events = [(ts - first_timestamp, addr, val) for ts, addr, val in sorted_events]
        
        self.start_time = time.time()
        self._log(f"Playback started at {time.strftime('%H:%M:%S')}")
        
        for rel_time, osc_address, value in relative_events:
            if not self.is_playing:
                break
            
            # Wait until it's time to send this event
            elapsed = time.time() - self.start_time
            wait_time = rel_time - elapsed
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            if not self.is_playing:
                break
            
            # Send the OSC message
            try:
                if value is None:
                    # Send empty message (no arguments) using OSCMessageBuilder
                    # SimpleUDPClient.send_message() requires at least one argument,
                    # so we build and send the message directly
                    msg_builder = OscMessageBuilder(osc_address)
                    # Don't add any arguments - message will have empty argument list
                    msg = msg_builder.build()
                    # Send directly using the client's socket
                    self.osc_client._sock.sendto(msg.dgram, (self.osc_ip, self.osc_port))
                    self._log(f"Sent: {osc_address} = (empty) at {rel_time:.6f}s")
                elif isinstance(value, bool):
                    self.osc_client.send_message(osc_address, value)
                    self._log(f"Sent: {osc_address} = {value} (bool) at {rel_time:.6f}s")
                elif isinstance(value, int):
                    self.osc_client.send_message(osc_address, value)
                    self._log(f"Sent: {osc_address} = {value} (int) at {rel_time:.6f}s")
                elif isinstance(value, float):
                    self.osc_client.send_message(osc_address, value)
                    self._log(f"Sent: {osc_address} = {value} (float) at {rel_time:.6f}s")
                elif isinstance(value, str):
                    self.osc_client.send_message(osc_address, value)
                    self._log(f"Sent: {osc_address} = {value} (str) at {rel_time:.6f}s")
                else:
                    # Fallback: send as string
                    self.osc_client.send_message(osc_address, str(value))
                    self._log(f"Sent: {osc_address} = {value} ({type(value).__name__}) at {rel_time:.6f}s")
                    
            except Exception as e:
                self._log(f"Error sending OSC message: {e}")
        
        if self.is_playing:
            self._log(f"Playback completed at {time.strftime('%H:%M:%S')}")
            self.is_playing = False
    
    def start_playback(self):
        """Start playback of the CSV events."""
        if self.is_playing:
            self._log("Playback is already running")
            return
        
        if not self.events:
            self._log("No events loaded. Please load a CSV file first.")
            return
        
        self.is_playing = True
        self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.playback_thread.start()
        self._log("Playback started")
    
    def stop_playback(self):
        """Stop playback of the CSV events."""
        if not self.is_playing:
            self._log("Playback is not running")
            return
        
        self.is_playing = False
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)
        self._log("Playback stopped")
    
    def _handle_control(self, osc_address: str, *args):
        """Handle OSC control commands."""
        if len(args) < 1:
            self._log(f"Invalid control command: {osc_address}")
            return
        
        command = args[0]
        
        if osc_address == "/playbackcsv":
            if command == 1 or command == 1.0:
                self.start_playback()
            elif command == 0 or command == 0.0:
                self.stop_playback()
            else:
                self._log(f"Unknown playback command: {command} (use 1 to start, 0 to stop)")
    
    def start_control_server(self):
        """Start the OSC control server."""
        disp = dispatcher.Dispatcher()
        disp.map("/playbackcsv", self._handle_control)
        
        try:
            server = osc_server.ThreadingOSCUDPServer(
                ("127.0.0.1", self.control_port), disp
            )
        except OSError as e:
            if e.errno == 48:  # Address already in use
                raise OSError(
                    f"Port {self.control_port} is already in use. "
                    f"Please use a different port with --control-port or close the other application."
                ) from e
            else:
                raise
        
        self._log(f"OSC control server started on 127.0.0.1:{self.control_port}")
        self._log(f"Send /playbackcsv 1 to start, /playbackcsv 0 to stop")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self._log("\nShutting down control server...")
            self.stop_playback()
            server.shutdown()


def main():
    parser = argparse.ArgumentParser(
        description="CSV OSC Player - Play OSC messages from a CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CSV Format:
  timestamp, osc_address, value
  
Example CSV:
  0.0, /test/int, 42
  1.5, /test/float, 3.14
  2.0, /test/int, 100

Control Commands (OSC):
  /playbackcsv 1  - Start playback
  /playbackcsv 0  - Stop playback
        """
    )
    
    parser.add_argument(
        "csv_file",
        help="Path to the CSV file"
    )
    
    parser.add_argument(
        "--osc-ip",
        default="127.0.0.1",
        help="Destination IP address for OSC messages (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--osc-port",
        type=int,
        default=8001,
        help="Destination port for OSC messages (default: 8001)"
    )
    
    parser.add_argument(
        "--control-port",
        type=int,
        default=8000,
        help="Port for OSC control server (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Create and initialize the player
    player = CSVOSCPlayer(args.csv_file, args.osc_ip, args.osc_port, args.control_port)
    
    try:
        # Load the CSV file
        player.load_csv()
        
        # Start the control server (this blocks)
        player.start_control_server()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        player.stop_playback()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

