import cv2
import numpy as np
from helpers import calculate_angle, calculate_psi

class GaugeReader:
    def __init__(self, min_angle, max_angle, min_val, max_val, needle_color='red'):
        """
        Initialize the GaugeReader with specific calibration for a gauge type.
        """
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.min_val = min_val
        self.max_val = max_val
        self.needle_color = needle_color
        
        # State variables to smooth jitter (Moving Average)
        self.psi_history = []
        self.history_size = 5

    def read_frame(self, frame):
        """
        Process a single frame (from video or image).
        Returns the calculated PSI value and the processed frame with overlays.
        """

        # 1. Pre-processing
        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Dynamic Resolution Logic (Normalization)
        min_dist = int(width * 0.25)
        min_radius = int(width * 0.05) # Reduced from 0.15 to 0.05 to detect smaller gauges
        
        # 2. Detect Circle
        circles = cv2.HoughCircles(
            blur, cv2.HOUGH_GRADIENT, dp=1, minDist=min_dist, 
            param1=80, param2=90, minRadius=min_radius, maxRadius=0
        )
        
        output_img = frame.copy()
        
        if circles is None:
            return None, output_img, None # No gauge found

        # Take the strongest circle found
        circles = np.uint16(np.around(circles))
        target = circles[0, 0]
        cx, cy, r = target[0], target[1], target[2]
        
        # Draw Gauge Boundary
        cv2.circle(output_img, (cx, cy), r, (0, 255, 0), 3)
        cv2.circle(output_img, (cx, cy), 5, (0, 0, 255), -1)
        
        # 3. Detect Needle
        needle_line = self._find_needle_line(frame, cx, cy, r)
        
        psi_val = None
        raw_angle = None
        
        if needle_line:
            x1, y1, x2, y2 = needle_line
            cv2.line(output_img, (x1, y1), (x2, y2), (0, 0, 255), 3)
            
            # 4. Math & Calibration
            raw_angle = calculate_angle(needle_line, cx, cy)
            raw_psi = calculate_psi(raw_angle, self.min_angle, self.max_angle, self.min_val, self.max_val)
            
            # 5. Signal Smoothing (Jitter Reduction)
            self.psi_history.append(raw_psi)
            if len(self.psi_history) > self.history_size:
                self.psi_history.pop(0)
            psi_val = round(sum(self.psi_history) / len(self.psi_history), 1)

            # If the reading is effectively zero (e.g., < 2% of range), force it to 0.0
            # This kills the "0.6, 0.8, 0.5" noise.
            if psi_val < 1.2:
                psi_val = 0.0
                
            # Draw Text
            cv2.putText(output_img, f"{psi_val} PSI", (cx - 40, cy + int(r/2)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

        return psi_val, output_img, raw_angle

    # Find the needle line in the frame
    def _find_needle_line(self, frame, cx, cy, r):

        # Masking to isolate gauge area
        mask = np.zeros(frame.shape[:2], dtype="uint8")

        cv2.circle(mask, (cx, cy), int(r * 1.0), 255, -1) 
        roi = cv2.bitwise_and(frame, frame, mask=mask)
        
        needle_mask = None
        
        if self.needle_color == 'black':
            # Color Thresholding for BLACK NEEDLE
            # Convert to Grayscale
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            # Inverse threshold: Dark pixels become white (255)
            _, needle_mask = cv2.threshold(gray_roi, 80, 255, cv2.THRESH_BINARY_INV)
            # Apply the circular mask again
            needle_mask = cv2.bitwise_and(needle_mask, needle_mask, mask=mask)
            
        elif self.needle_color == 'blue':
            # Color Thresholding for BLUE NEEDLE
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            lower_blue = np.array([100, 150, 50])
            upper_blue = np.array([140, 255, 255])
            needle_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
        else: # Default to 'red'
            # Color Thresholding for RED NEEDLE
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # Lower Red Mask (0-10)
            lower1 = np.array([0, 100, 100])
            upper1 = np.array([10, 255, 255])
            mask1 = cv2.inRange(hsv, lower1, upper1)
            
            # Upper Red Mask (170-180)
            lower2 = np.array([170, 100, 100])
            upper2 = np.array([180, 255, 255])
            mask2 = cv2.inRange(hsv, lower2, upper2)
            
            # Combine them
            needle_mask = cv2.bitwise_or(mask1, mask2)
        
        # 3. Line Detection 
        lines = cv2.HoughLinesP(
            needle_mask, rho=1, theta=np.pi / 180, threshold=15, 
            minLineLength=int(r * 0.10), maxLineGap=int(r * 0.10)
        )
        
        if lines is None: return None
        
       # 4. Filter for "Best Reach" 
        best_line = None
        max_reach = 0 # We want the line that reaches closest to the edge (radius)
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Calculate distance from center to line
            num = abs((y2 - y1) * cx - (x2 - x1) * cy + x2 * y1 - y2 * x1)
            den = np.sqrt((y2 - y1)**2 + (x2 - x1)**2)
            if den == 0 or (num / den) > 15: 
                continue 
        
            # Calculate how far each endpoint is from the center hub
            dist1 = np.sqrt((x1 - cx)**2 + (y1 - cy)**2)
            dist2 = np.sqrt((x2 - cx)**2 + (y2 - cy)**2)
            
            # Finds which end is furthest out
            current_tip_dist = max(dist1, dist2)
            
            # If the CLOSEST point is too far from center (>30% radius), 
            # it's probably floating text, not the needle.
            closest_dist = min(dist1, dist2)
            if closest_dist > (r * 0.30):
                continue

            # Pick the line that extends furthest towards the edge
            if current_tip_dist > max_reach:
                max_reach = current_tip_dist
                best_line = (x1, y1, x2, y2)
                
        return best_line