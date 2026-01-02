import json
import csv
import time
import os

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file

    # Save configuration to a JSON file
    def save_config(self, config_data):
       
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    # Load configuration from a JSON file if existing, if not default values are used
    def load_config(self):
        
        if not os.path.exists(self.config_file):
            return None
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return None

class DataLogger:
    def __init__(self, log_file='telemetry_log.csv'):
        self.log_file = log_file
        self.start_time = time.time()
        
        # Initialize file with headers
        try:
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'PSI'])
            print(f"Data logging started: {self.log_file}")
        except Exception as e:
            print(f"Error initializing log file: {e}")

    # Log elapsed time and PSI value to CSV
    def log(self, psi_value):

        if psi_value is None:
            return

        elapsed_time = time.time() - self.start_time
        try:
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([f"{elapsed_time:.2f}", f"{psi_value:.2f}"])
        except Exception as e:
            print(f"Error logging data: {e}")
