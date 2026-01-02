import json
import csv
import time
import os

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file

    def save_config(self, config_data):
        """
        Saves the calibration dictionary to a JSON file.
        config_data should be a dictionary containing:
        - needle_color
        - min_angle
        - max_angle
        - min_psi
        - max_psi
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def load_config(self):
        """
        Loads the configuration from the JSON file.
        Returns the dictionary if file exists, else None.
        """
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

    def log(self, psi_value):
        """
        Logs the current elapsed time and PSI value to the CSV file.
        """
        if psi_value is None:
            return

        elapsed_time = time.time() - self.start_time
        try:
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([f"{elapsed_time:.2f}", f"{psi_value:.2f}"])
        except Exception as e:
            print(f"Error logging data: {e}")
