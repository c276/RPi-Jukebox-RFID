import math
import mpu6050
import json
import sys
import time
from typing import Dict, Tuple

CALIBRATION_FILE = 'mpu6050_calibration.json'

# Define a function to read the sensor data
def read_sensor_data() -> Tuple[Dict, Dict, Dict]:
    """Reads the accelerometer, gyroscope, and temperature data from the MPU6050 sensor."""
    # Create a new Mpu6050 object
    sensor = mpu6050.mpu6050(0x68)

    # Read the sensor values
    accelerometer_data = sensor.get_accel_data()
    gyroscope_data = sensor.get_gyro_data()
    temperature = sensor.get_temp()

    return {
        'accelerometer': accelerometer_data,
        'gyroscope': gyroscope_data,
        'temperature': temperature
    }


def calibrate_sensor(calibration_file=CALIBRATION_FILE):
    """
    Reads current sensor values and saves them to a JSON file for calibration reference.

    Example json:
    {
        "accelerometer": {
            "x": -0.9337386474609375,
            "y": -9.435548742675781,
            "z": -1.9728221679687499
        },
        "gyroscope": {
            "x": 0.9694656488549618,
            "y": 1.9083969465648856,
            "z": 0.22137404580152673
        },
        "temperature": 49.65941176470588,
        "timestamp": 1750250015.9694533
    }
    """
    try:
        current_data = read_sensor_data()
        calibration_data = {
            'accelerometer': current_data["accelerometer"],
            'gyroscope': current_data["gyroscope"],
            'temperature': current_data["temperature"],
            'timestamp': time.time()
        }
        with open(calibration_file, 'w') as f:
            json.dump(calibration_data, f, indent=4)
        print(f"Calibration complete. Data saved to {calibration_file}")
    except OSError:
        print("Sensor connection error during calibration.")


def get_calibrated_data(calibration_file=CALIBRATION_FILE):
    """
    Reads current sensor data and calibration zero from file,
    returns a dict with calibrated values (current - sensor_reference).
    """
    # Read current sensor data
    current_data = read_sensor_data()

    # Read calibration zero from file
    with open(calibration_file, 'r') as f:
        sensor_reference = json.load(f)

    # Subtract calibration zero from current data
    calibrated = {
        'accelerometer': {
            axis: current_data['accelerometer'][axis] - sensor_reference['accelerometer'][axis]
            for axis in current_data['accelerometer']
        },
        'gyroscope': {
            axis: current_data['gyroscope'][axis] - sensor_reference['gyroscope'][axis]
            for axis in current_data['gyroscope']
        },
        'temperature': current_data['temperature']
    }
    return calibrated


def detect_tilt_threshold(calibrated_data, threshold=3.0):
    """
    Detects tilt direction based on calibrated accelerometer data.
    Returns one of: 'left', 'right', 'top', 'bottom', or None if no significant tilt.
    threshold: minimum absolute value (in m/s^2) to consider as a tilt.
    """
    accel = calibrated_data['accelerometer']
    x = accel['x']
    y = accel['y']

    if abs(x) > abs(y):
        if x > threshold:
            return 'right'
        elif x < -threshold:
            return 'left'
    else:
        if y > threshold:
            return 'top'
        elif y < -threshold:
            return 'bottom'
    return None


def detect_tilt_angle(calibrated_data, angle_threshold=40.0):
    """
    Detects tilt direction based on calibrated accelerometer data.
    Returns one of: 'left', 'right', 'top', 'bottom', or None if no significant tilt.
    angle_threshold: minimum tilt angle in degrees to consider as a tilt.
    """
    accel = calibrated_data['accelerometer']
    x = accel['x']
    y = accel['y']
    z = accel['z']

    # Calculate tilt angles in degrees
    # Roll: rotation around X axis (left/right tilt)
    # Pitch: rotation around Y axis (top/bottom tilt)
    roll = math.degrees(math.atan2(y, z))
    pitch = math.degrees(math.atan2(-x, math.sqrt(y * y + z * z)))

    if abs(roll) > abs(pitch):
        if roll > angle_threshold:
            return 'left'
        elif roll < -angle_threshold:
            return 'right'
    else:
        if pitch > angle_threshold:
            return 'top'
        elif pitch < -angle_threshold:
            return 'bottom'
    return None


def detect_knock(calibrated_data, accel_threshold=8.0):
    """
    Detects a knock direction based on a sudden spike in calibrated accelerometer data.
    Returns one of: 'knock_left', 'knock_right', 'knock_top', 'knock_bottom', or None if no knock detected.
    accel_threshold: minimum absolute acceleration (in m/s^2) to consider as a knock.
    """
    accel = calibrated_data['accelerometer']
    x = accel['x']
    y = accel['y']

    if abs(x) > abs(y):
        if x > accel_threshold:
            return 'knock_right'
        elif x < -accel_threshold:
            return 'knock_left'
    else:
        if y > accel_threshold:
            return 'knock_top'
        elif y < -accel_threshold:
            return 'knock_bottom'
    return None


if __name__ == "__main__":
    # Check if the script is run with 'calibrate' argument
    if len(sys.argv) > 1 and sys.argv[1] == 'calibrate':
        calibrate_sensor()
        sys.exit(0)

    # Start a while loop to continuously read the sensor data
    try:
        while True:
            try:
                current_data = read_sensor_data()
                print("Current sensor data:", current_data)
            except OSError:
                print("Connection lost. Retry")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping due to keyboard interrupt.")
        sys.exit(0)
