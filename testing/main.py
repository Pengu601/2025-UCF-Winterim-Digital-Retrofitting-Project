from gauge import calibrate_gauge_static
import os

# Point to your asset image
# Ensure the path matches your actual folder structure
image_path = os.path.join("assets", "gauge_test_2.jpg") 
absolute_path = os.path.abspath(image_path)
if __name__ == "__main__":
    calibrate_gauge_static(absolute_path)

    