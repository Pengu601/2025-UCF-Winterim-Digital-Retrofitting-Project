import cv2
import os
import matplotlib.pyplot as plt
from gauge import GaugeReader
from dashboard import Dashboard
from data_manager import ConfigManager, DataLogger
from camera import ThreadedCamera

def run_live_demo():
    # Load Configuration on startup
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    # Default values if no config exists
    current_config = {
        'min_angle': 0,
        'max_angle': 0,
        'min_psi': 0,
        'max_psi': 100,
        'needle_color': 'red'
    }
    
    if config:
        print("Loaded configuration from file.")
        current_config.update(config)
    else:
        print("No configuration found. Please calibrate the gauge.")

    # Initialize Gauge Reader (OpenCV Processing)
    reader = GaugeReader(
        current_config['min_angle'], 
        current_config['max_angle'], 
        current_config['min_psi'], 
        current_config['max_psi'], 
        needle_color=current_config['needle_color']
    )
    
    logger = DataLogger()
    
    def save_current_config():
        # Helper to save current state of reader
        cfg = {
            'min_angle': reader.min_angle,
            'max_angle': reader.max_angle,
            'min_psi': reader.min_val,
            'max_psi': reader.max_val,
            'needle_color': reader.needle_color
        }
        config_manager.save_config(cfg)

    # Update Needle Color
    def on_config_change(new_color):
        print(f"Main: Updating needle color to {new_color}")
        reader.needle_color = new_color
        save_current_config()

    # Update config with new calibration values
    def on_calibration_complete(min_angle, max_angle, min_psi, max_psi):
        print(f"Main: Calibration Updated!")
        print(f"  Min Angle: {min_angle:.1f}, Max Angle: {max_angle:.1f}")
        print(f"  Min PSI: {min_psi}, Max PSI: {max_psi}")
        
        # Update Reader
        reader.min_angle = min_angle
        reader.max_angle = max_angle
        reader.min_val = min_psi
        reader.max_val = max_psi
        
        # Update Dashboard Static Lines
        dashboard.min_angle = min_angle
        dashboard.max_angle = max_angle
        
        # Save to JSON
        save_current_config()

    def on_min_angle_update(min_angle):
        print(f"Main: Updating Min Angle to {min_angle:.1f}")
        reader.min_angle = min_angle
        dashboard.min_angle = min_angle

    # Setup Webcam Feed and Dashboard

    video_stream = ThreadedCamera(0).start()
    
    dashboard = Dashboard(
        config_callback=on_config_change, 
        calibration_callback=on_calibration_complete, 
        min_angle_callback=on_min_angle_update,
        min_angle=current_config['min_angle'],
        max_angle=current_config['max_angle']
    )

    print("Starting Live Feed... Close the dashboard window to quit.")

    # Running Loop until program is closed or exited
    while True:
        ret, frame = video_stream.read()
        if not ret:
            # If no frame is ready yet or camera disconnected
            continue

        # Process frame
        psi, processed_frame, raw_angle = reader.read_frame(frame)
        
        # Log Data
        if psi is not None:
            logger.log(psi)
        
        # Update Dashboard
        dashboard.update(processed_frame, psi, raw_angle)
        
        # Check if dashboard window is closed
        if not plt.fignum_exists(dashboard.fig.number):
            break

    video_stream.stop()
    

if __name__ == "__main__":
    # If you don't have a webcam right now, you can still test on an image:
    # Just load an image and pass it to reader.read_frame() like before!
    
    # Example: 
    # img = cv2.imread('test_gauge.jpg')
    # psi, processed_img, angle = reader.read_frame(img)
    # print(f"Detected PSI: {psi}, Angle: {angle}")

    run_live_demo()