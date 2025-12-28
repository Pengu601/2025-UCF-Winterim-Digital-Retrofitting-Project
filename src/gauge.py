import cv2
import numpy as np
import matplotlib.pyplot as plt
def calibrate_gauge_static(image_path):

    img = cv2.imread(image_path)

    if img is None:
        print("Error: Could not read image.")
        return
    
    image_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # Conver to grayscale (HoughCircles only works in Grayscale)

    image_blur = cv2.GaussianBlur(image_gray, (9, 9), 2) # Apply Gaussian Blur to reduce noise and improve circle detection

    detected_gauges = cv2.HoughCircles(image_blur, cv2.HOUGH_GRADIENT, dp=1, minDist=100, param1=80, param2=90, minRadius=400, maxRadius=0)
    
    output_image = image_blur.copy()

    if detected_gauges is not None:
        
        detected_gauges = np.uint16(np.around(detected_gauges))

        for i in detected_gauges[0, :]:
            center_x, center_y, radius = i[0], i[1], i[2]
            
            # Draw the outer circle (Green)
            cv2.circle(output_image, (center_x, center_y), radius, (0, 255, 0), 3)
            # Draw the center point (Red)
            cv2.circle(output_image, (center_x, center_y), 5, (0, 0, 255), -1)
            
            print(f"Gauge Detected! Center: ({center_x}, {center_y}), Radius: {radius}")

        img_rgb_original = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_rgb_output = cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
        plt.figure(figsize=(10, 5))

        plt.subplot(1, 2, 1)
        plt.title('Original Image')
        plt.imshow(img_rgb_original)
        plt.axis('off')

        plt.subplot(1, 2, 2)
        plt.title('Detected Gauges')
        plt.imshow(img_rgb_output)
        plt.axis('off')

        plt.show()


