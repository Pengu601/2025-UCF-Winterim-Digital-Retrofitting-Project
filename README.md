# Optical Telemetry Bridge

**Optical Telemetry Bridge** is a computer vision application designed to digitize analog gauge readings in real-time. By processing a live webcam feed, the system tracks the needle's angle, converts it to a PSI value, and visualizes the data on a live telemetry dashboard.


## Installation & Setup

### 1. Prerequisites
* Python 3.8 or higher installed on your system.
* A webcam connected to your computer.

### 2. Set Up Virtual Environment (Recommended)
It is best practice to run this project in an isolated virtual environment to prevent conflicts with other Python projects.

**On Windows:**
```bash
# Create the environment
python -m venv venv

# Activate the environment
.\venv\Scripts\activate
```
**On Mac:**
```bash
# Create the environment
python3 -m venv venv

# Activate the environment
source venv/bin/activate
```

### 3. Install Dependencies
Once the virtual environment is active, install the required libraries (OpenCV, Matplotlib, Numpy) using the requirements file:

```Bash

pip install -r requirements.txt
```
### 4. How to Run the Program
Ensure your virtual environment is active (you should see (venv) in your terminal prompt) and your webcam is plugged in.

Run the main application script:

```Bash

python src/main.py
```
### 5. First-Time Startup: Calibration Wizard
On the very first launch (or if the config.json file is deleted), you will need to calibrate the gauge to be able to get correct PSI readings. You must complete this one-time setup to "teach" the software how to read your specific gauge.

Follow the on screen steps to properly calibrate your specific gauge to work with the program.

### Outputs & Files

#### telemetry_log.csv: 
This file is generated automatically in the project folder. It contains a full log of your session:

    Timestamp: Seconds elapsed since start.

    PSI: The pressure reading at that moment.

#### config.json: 
Stores your saved calibration profile. Delete this file if you need to re-calibrate for a new gauge.

### Controls
q: Quit the application safely and save the data log.
