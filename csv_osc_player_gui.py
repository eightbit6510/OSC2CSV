#!/usr/bin/env python3
"""
CSV OSC Player GUI
A graphical interface for the CSV OSC Player.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from csv_osc_player import CSVOSCPlayer
from osc_recorder import OSCRecorder


class CSVOSCPlayerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV OSC Player & Recorder")
        self.root.geometry("800x750")
        
        self.player: CSVOSCPlayer = None
        self.control_server_thread: threading.Thread = None
        self.control_server = None
        
        self.recorder: OSCRecorder = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # File selection
        ttk.Label(main_frame, text="CSV File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.csv_file_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.csv_file_var, width=50).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(main_frame, text="Browse...", command=self.browse_csv_file).grid(
            row=0, column=2, pady=5
        )
        
        # Load button
        ttk.Button(main_frame, text="Load CSV", command=self.load_csv).grid(
            row=1, column=0, columnspan=3, pady=10
        )
        
        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )
        
        # OSC Configuration
        config_frame = ttk.LabelFrame(main_frame, text="OSC Configuration", padding="10")
        config_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        config_frame.columnconfigure(1, weight=1)
        
        ttk.Label(config_frame, text="Destination IP:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.osc_ip_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(config_frame, textvariable=self.osc_ip_var, width=20).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5
        )
        
        ttk.Label(config_frame, text="Destination Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.osc_port_var = tk.StringVar(value="8001")
        ttk.Entry(config_frame, textvariable=self.osc_port_var, width=20).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5
        )
        
        ttk.Label(config_frame, text="Control Port:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.control_port_var = tk.StringVar(value="8000")
        ttk.Entry(config_frame, textvariable=self.control_port_var, width=20).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=5
        )
        
        ttk.Button(config_frame, text="Apply Settings", command=self.apply_settings).grid(
            row=3, column=0, columnspan=2, pady=10
        )
        
        # Playback controls
        control_frame = ttk.LabelFrame(main_frame, text="Playback Controls", padding="10")
        control_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.start_button = ttk.Button(
            control_frame, text="Start", command=self.start_playback, state=tk.DISABLED
        )
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_button = ttk.Button(
            control_frame, text="Stop", command=self.stop_playback, state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )
        
        # Recording Configuration
        record_config_frame = ttk.LabelFrame(main_frame, text="Recording Configuration", padding="10")
        record_config_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        record_config_frame.columnconfigure(1, weight=1)
        
        ttk.Label(record_config_frame, text="Recording Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.recording_name_var = tk.StringVar(value="agat")
        ttk.Entry(record_config_frame, textvariable=self.recording_name_var, width=20).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5
        )
        ttk.Label(record_config_frame, text="(used as filename prefix)", font=("TkDefaultFont", 8)).grid(
            row=0, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        ttk.Label(record_config_frame, text="Listen IP:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.record_ip_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(record_config_frame, textvariable=self.record_ip_var, width=20).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5
        )
        
        ttk.Label(record_config_frame, text="Listen Port:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.record_port_var = tk.StringVar(value="8002")
        ttk.Entry(record_config_frame, textvariable=self.record_port_var, width=20).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=5
        )
        
        ttk.Label(record_config_frame, text="Output Directory:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value=".")
        ttk.Entry(record_config_frame, textvariable=self.output_dir_var, width=40).grid(
            row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(record_config_frame, text="Browse...", command=self.browse_output_dir).grid(
            row=3, column=2, pady=5
        )
        
        # Recording controls
        record_control_frame = ttk.LabelFrame(main_frame, text="Recording Controls", padding="10")
        record_control_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.record_start_button = ttk.Button(
            record_control_frame, text="Start Recording", command=self.start_recording
        )
        self.record_start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.record_stop_button = ttk.Button(
            record_control_frame, text="Stop Recording", command=self.stop_recording, state=tk.DISABLED
        )
        self.record_stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.recording_status_label = ttk.Label(record_control_frame, text="Not recording", foreground="gray")
        self.recording_status_label.grid(row=0, column=2, padx=10, pady=5)
        
        # Status
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        self.status_text = scrolledtext.ScrolledText(
            status_frame, height=12, width=80, wrap=tk.WORD
        )
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.status_text.config(state=tk.DISABLED)
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
    def log(self, message):
        """Add a message to the status text area."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        
    def update_status_bar(self, message):
        """Update the status bar."""
        self.status_bar.config(text=message)
        
    def browse_csv_file(self):
        """Open file dialog to select CSV file."""
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.csv_file_var.set(filename)
    
    def browse_output_dir(self):
        """Open directory dialog to select output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)
            
    def validate_settings(self):
        """Validate OSC settings."""
        try:
            osc_ip = self.osc_ip_var.get().strip()
            osc_port = int(self.osc_port_var.get().strip())
            control_port = int(self.control_port_var.get().strip())
            
            if osc_port < 1 or osc_port > 65535:
                raise ValueError("OSC port must be between 1 and 65535")
            if control_port < 1 or control_port > 65535:
                raise ValueError("Control port must be between 1 and 65535")
                
            return osc_ip, osc_port, control_port
        except ValueError as e:
            messagebox.showerror("Invalid Settings", str(e))
            return None
            
    def apply_settings(self):
        """Apply OSC settings."""
        settings = self.validate_settings()
        if settings is None:
            return
            
        osc_ip, osc_port, control_port = settings
        
        # Stop existing server if running
        if self.control_server:
            self.log("Stopping existing control server...")
            self.stop_control_server()
        
        # Create new player with updated settings
        csv_file = self.csv_file_var.get().strip()
        if csv_file:
            try:
                self.player = CSVOSCPlayer(csv_file, osc_ip, osc_port, control_port, status_callback=self.log)
                self.log(f"Settings applied: OSC {osc_ip}:{osc_port}, Control port: {control_port}")
                self.start_control_server()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply settings: {e}")
        else:
            self.log(f"Settings saved: OSC {osc_ip}:{osc_port}, Control port: {control_port}")
            messagebox.showinfo("Settings", "Settings saved. Load a CSV file to use them.")
            
    def load_csv(self):
        """Load the selected CSV file."""
        csv_file = self.csv_file_var.get().strip()
        if not csv_file:
            messagebox.showerror("Error", "Please select a CSV file first.")
            return
            
        settings = self.validate_settings()
        if settings is None:
            return
            
        osc_ip, osc_port, control_port = settings
        
        try:
            # Create player and load CSV
            self.player = CSVOSCPlayer(csv_file, osc_ip, osc_port, control_port, status_callback=self.log)
            self.player.load_csv()
            
            self.log(f"Loaded CSV: {csv_file}")
            self.log(f"Events loaded: {len(self.player.events)}")
            self.update_status_bar(f"Loaded {len(self.player.events)} events")
            
            # Enable playback controls
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            
            # Start control server
            self.start_control_server()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")
            self.log(f"Error: {e}")
            
    def start_control_server(self):
        """Start the OSC control server in a separate thread."""
        if self.player is None:
            return
            
        if self.control_server_thread and self.control_server_thread.is_alive():
            return
            
        def run_server():
            from pythonosc import dispatcher, osc_server
            
            disp = dispatcher.Dispatcher()
            disp.map("/playbackcsv", self.player._handle_control)
            
            try:
                self.control_server = osc_server.ThreadingOSCUDPServer(
                    ("127.0.0.1", self.player.control_port), disp
                )
                self.log(f"OSC control server started on 127.0.0.1:{self.player.control_port}")
                self.log("Send /playbackcsv 1 to start, /playbackcsv 0 to stop")
                self.control_server.serve_forever()
            except OSError as e:
                if e.errno == 48:
                    self.log(f"Warning: Control port {self.player.control_port} already in use")
                else:
                    self.log(f"Error starting control server: {e}")
            except Exception as e:
                self.log(f"Control server error: {e}")
        
        self.control_server_thread = threading.Thread(target=run_server, daemon=True)
        self.control_server_thread.start()
        
    def stop_control_server(self):
        """Stop the OSC control server."""
        if self.control_server:
            self.control_server.shutdown()
            self.control_server = None
            self.log("Control server stopped")
            
    def start_playback(self):
        """Start playback."""
        if self.player is None:
            messagebox.showerror("Error", "Please load a CSV file first.")
            return
            
        try:
            self.player.start_playback()
            self.log("Playback started")
            self.update_status_bar("Playing...")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # Start monitoring playback status
            self.monitor_playback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start playback: {e}")
            self.log(f"Error: {e}")
            
    def stop_playback(self):
        """Stop playback."""
        if self.player:
            self.player.stop_playback()
            self.log("Playback stopped")
            self.update_status_bar("Stopped")
            self.start_button.config(state=tk.NORMAL)
            
    def monitor_playback(self):
        """Monitor playback status and update UI."""
        if self.player and self.player.is_playing:
            self.root.after(100, self.monitor_playback)
        else:
            if self.player:
                self.update_status_bar("Ready")
                self.start_button.config(state=tk.NORMAL)
                
    def validate_recording_settings(self):
        """Validate recording settings."""
        try:
            recording_name = self.recording_name_var.get().strip()
            listen_ip = self.record_ip_var.get().strip()
            listen_port = int(self.record_port_var.get().strip())
            output_dir = self.output_dir_var.get().strip()
            
            if not recording_name:
                raise ValueError("Recording name cannot be empty")
            if listen_port < 1 or listen_port > 65535:
                raise ValueError("Listen port must be between 1 and 65535")
            if not output_dir:
                output_dir = "."
            
            return recording_name, listen_ip, listen_port, output_dir
        except ValueError as e:
            messagebox.showerror("Invalid Settings", str(e))
            return None
    
    def start_recording(self):
        """Start recording OSC messages."""
        # Check if already recording
        if self.recorder and self.recorder.is_recording:
            messagebox.showwarning("Already Recording", "Recording is already in progress.")
            return
        
        settings = self.validate_recording_settings()
        if settings is None:
            return
        
        recording_name, listen_ip, listen_port, output_dir = settings
        
        try:
            # Create or update recorder
            if self.recorder:
                # Update settings if changed
                if (self.recorder.listen_ip != listen_ip or 
                    self.recorder.listen_port != listen_port or
                    self.recorder.recording_name != recording_name):
                    # Stop old server if running
                    if self.recorder.server:
                        self.recorder.stop_server()
                    self.recorder = OSCRecorder(listen_ip, listen_port, recording_name, status_callback=self.log)
                    self.recorder.start_server()
                else:
                    # Just update the name
                    self.recorder.recording_name = recording_name
            else:
                self.recorder = OSCRecorder(listen_ip, listen_port, recording_name, status_callback=self.log)
                self.recorder.start_server()
            
            # Start recording
            self.recorder.start_recording(output_dir)
            
            self.record_start_button.config(state=tk.DISABLED)
            self.record_stop_button.config(state=tk.NORMAL)
            self.recording_status_label.config(text="Recording...", foreground="red")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start recording: {e}")
            self.log(f"Error: {e}")
    
    def stop_recording(self):
        """Stop recording OSC messages."""
        if self.recorder:
            try:
                self.recorder.stop_recording()
                filepath = self.recorder.get_recording_filepath()
                if filepath:
                    self.log(f"Recording saved to: {filepath}")
                
                self.record_start_button.config(state=tk.NORMAL)
                self.record_stop_button.config(state=tk.DISABLED)
                self.recording_status_label.config(text="Not recording", foreground="gray")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to stop recording: {e}")
                self.log(f"Error: {e}")
    
    def on_closing(self):
        """Handle window closing."""
        if self.player:
            self.player.stop_playback()
        if self.recorder:
            self.recorder.stop_recording()
            self.recorder.stop_server()
        self.stop_control_server()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = CSVOSCPlayerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

