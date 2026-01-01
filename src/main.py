import cv2
import os
from gauge import GaugeReader
from dashboard import TelemetryGraph
# --- CONFIGURATION ---
# Use the values you just successfully calibrated!
CALIB_MIN_ANGLE = 190.6
CALIB_MAX_ANGLE = 310.6
MIN_PSI = 0
MAX_PSI = 100

def run_live_demo():
    # 1. Initialize the Reader Object
    reader = GaugeReader(CALIB_MIN_ANGLE, CALIB_MAX_ANGLE, MIN_PSI, MAX_PSI)
    
    # 2. Setup Webcam (0 is usually the default camera)
    cap = cv2.VideoCapture(0)
    
    graph = TelemetryGraph()
    # Optional: Set resolution for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("Starting Live Feed... Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 3. Ask the Reader to process this frame
        psi, processed_frame = reader.read_frame(frame)
        
        if psi is not None:
            print(f"Current Reading: {psi} PSI")
            graph.update(psi)
        # 4. Show the result
        cv2.imshow("Optical Telemetry Bridge", processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # If you don't have a webcam right now, you can still test on an image:
    # Just load an image and pass it to reader.read_frame() like before!
    run_live_demo()