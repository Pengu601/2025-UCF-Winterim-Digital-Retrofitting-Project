import cv2
import numpy as np
import matplotlib.pyplot as plt
from helpers import calculate_angle, calculate_psi

# --- CALIBRATION CONFIGURATION ---
# Based on your gauge image (Geo-Flo):
# 0 PSI (Bottom Left) is roughly 225 degrees in standard math.
# 100 PSI (Bottom Right) is roughly 315 degrees in standard math.
MIN_ANGLE = 217.6
MAX_ANGLE = 310.6
MIN_VAL = 0
MAX_VAL = 100

def calibrate_gauge_static(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not read image.")
        return
    
    # (Keep your existing Circle Detection code unchanged)
    image_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
    image_blur = cv2.GaussianBlur(image_gray, (9, 9), 2) 
    height, width = img.shape[:2]
    minDist = int(width * .25)
    minRadius = int(width * .15)
    
    detected_gauges = cv2.HoughCircles(
        image_blur, cv2.HOUGH_GRADIENT, dp=1, minDist=minDist, 
        param1=80, param2=90, minRadius=minRadius, maxRadius=0
    )
    
    output_image = img.copy()

    if detected_gauges is not None:
        detected_gauges = np.uint16(np.around(detected_gauges))

        for i in detected_gauges[0, :]:
            center_x, center_y, radius = i[0], i[1], i[2]
            
            # Draw Gauge Circle
            cv2.circle(output_image, (center_x, center_y), radius, (0, 255, 0), 3)
            cv2.circle(output_image, (center_x, center_y), 5, (0, 0, 255), -1)
            
            # Call Needle Detection
            needle_coords, needle_mask = detect_needle(img, center_x, center_y, radius)

            if needle_coords:
                x1, y1, x2, y2 = needle_coords
                cv2.line(output_image, (x1, y1), (x2, y2), (0, 0, 255), 3)
                
                # --- NEW: CALCULATE PSI ---
                angle = calculate_angle(needle_coords, center_x, center_y)
                psi = calculate_psi(angle, MIN_ANGLE, MAX_ANGLE, MIN_VAL, MAX_VAL)
                
                print(f"Angle: {angle:.1f}° -> PSI: {psi}")
                
                # Draw Text on Screen
                cv2.putText(output_image, f"{psi} PSI", (center_x - 40, center_y + int(radius/2)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            else:
                print("Gauge found, but no needle.")

            # --- VISUAL CALIBRATION TEST ---
            # 1. Calculate the coordinates for the "Max Angle" (Theoretical 100 PSI)
            # We use trigonometry to find the endpoint of this imaginary line
            max_angle_rad = np.radians(MAX_ANGLE)
            
            # Note: In images, Y grows downwards, so we subtract sin for 'up' 
            # (depending on your coordinate system logic). 
            # Let's use standard polar conversion relative to the center:
            # x = center_x + radius * cos(angle)
            # y = center_y - radius * sin(angle)  <-- Subtract because Y is inverted in images
            
            # HOWEVER, your 'calculate_angle' function outputted standard degrees (0-360).
            # We need to reverse-engineer the position.
            
            # Simpler way: Just guess and check.
            # Convert degrees back to radians for drawing
            # Be careful with direction: OpenCV cos/sin usually assume 0 is East, going Clockwise?
            # Actually, let's stick to the coordinate math used in 'calculate_angle' reversed.
            
            # X = Center + Radius * Cos(radians)
            # Y = Center - Radius * Sin(radians) (assuming standard Cartesian inverted for screen)
            
            # Since our angle system was: 0=Right, 90=Up, 180=Left, 270=Down
            # But the 'calculate_angle' returns 0-360 positive.
            # Let's try drawing it:
            
            max_pt_x = int(center_x + radius * np.cos(np.radians(360 - MAX_ANGLE)))
            max_pt_y = int(center_y + radius * np.sin(np.radians(360 - MAX_ANGLE)))
            
            # Draw the "Theoretical Max" line in BLUE
            cv2.line(output_image, (center_x, center_y), (max_pt_x, max_pt_y), (255, 0, 0), 2)
            cv2.putText(output_image, "MAX CALIB", (max_pt_x-20, max_pt_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        # (Keep your existing Visualization code unchanged)
        img_rgb_original = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_rgb_output = cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
        
        plt.figure(figsize=(15, 5))
        plt.subplot(1, 3, 1); plt.imshow(img_rgb_original); plt.axis('off')
        plt.subplot(1, 3, 2); plt.imshow(img_rgb_output); plt.axis('off')
        plt.subplot(1, 3, 3); 
        if 'needle_mask' in locals(): plt.imshow(needle_mask, cmap='gray')
        plt.axis('off')
        plt.show()
    else:
        print("No gauges detected.")

# (Keep your detect_needle function exactly as it was in your file)
def detect_needle(frame, center_x, center_y, radius):
    # ... (Paste your existing detect_needle function here) ...
    # This part was already perfect in your upload!
    mask = np.zeros(frame.shape[:2], dtype="uint8")
    cv2.circle(mask, (center_x, center_y), int(radius * 0.9), 255, -1)
    gauge_roi = cv2.bitwise_and(frame, frame, mask=mask)
    hsv = cv2.cvtColor(gauge_roi, cv2.COLOR_BGR2HSV)
    lower = np.array([0, 0, 0])
    upper = np.array([180, 255, 100])
    needle_mask = cv2.inRange(hsv, lower, upper)
    lines = cv2.HoughLinesP(needle_mask, rho=1, theta=np.pi / 180, threshold=15, 
                            minLineLength=int(radius * 0.10), maxLineGap=int(radius * 0.05))

    if lines is None: return None, needle_mask

    best_line = None
    max_len = 0

    for line in lines:
        x1, y1, x2, y2 = line[0]
        numerator = abs((y2 - y1) * center_x - (x2 - x1) * center_y + x2 * y1 - y2 * x1)
        denominator = np.sqrt((y2 - y1)**2 + (x2 - x1)**2)
        if denominator == 0: continue
        dist_from_center = numerator / denominator
        if dist_from_center > 10: continue 
        line_len = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if line_len > max_len:
            max_len = line_len
            best_line = (x1, y1, x2, y2)

    return best_line, needle_mask