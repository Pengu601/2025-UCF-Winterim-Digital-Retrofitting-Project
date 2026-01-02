import numpy as np

# Calculate the angle of the needle relative to the center of the gauge
def calculate_angle(line, center_x, center_y):

    if line is None:
        return None

    x1, y1, x2, y2 = line
    dist1 = np.sqrt((x1 - center_x)**2 + (y1 - center_y)**2)
    dist2 = np.sqrt((x2 - center_x)**2 + (y2 - center_y)**2)
    
    if dist1 > dist2:
        tip_x, tip_y = x1, y1
    else:
        tip_x, tip_y = x2, y2

    delta_y = center_y - tip_y 
    delta_x = tip_x - center_x
    
    angle_rad = np.arctan2(delta_y, delta_x)
    angle_deg = np.degrees(angle_rad)
    
    if angle_deg < 0:
        angle_deg += 360
        
    return angle_deg

# Calculate PSI based on needle angle and calibration
def calculate_psi(current_angle, start_angle, end_angle, min_val, max_val):
    """
    
    Meaning of variables:
        current_angle - The needle's current angle (0-360).
        start_angle - The angle of the '0 PSI' mark (e.g., ~225 deg).
        end_angle - The angle of the '100 PSI' mark (e.g., ~315 deg).
        min_val - The value at start (0).
        max_val - The value at end (100).
    """
    # 1. Calculate the total "arc" of the gauge
    diff_total = start_angle - end_angle
    if diff_total < 0:
        diff_total += 360
        
    # 2. Calculate how far the needle has traveled
    diff_current = start_angle - current_angle
    if diff_current < 0:
        diff_current += 360
        
    # Deadzone logic
    # If diff_current is larger than the total range, it means we are in the "dead zone"
    if diff_current > diff_total:
        dead_zone = 360 - diff_total
        dist_from_max = diff_current - diff_total
        
        # If closer to Max (just passed 100%), clamp to Max
        if dist_from_max < (dead_zone / 2):
            return max_val
        # If closer to Min (just before 0%), clamp to Min
        else:
            return min_val

    # 3. Calculate Percentage
    percentage = diff_current / diff_total
    
    # 4. Map to PSI
    psi = min_val + (percentage * (max_val - min_val))
    
    return round(psi, 1)