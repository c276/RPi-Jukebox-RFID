import os
from datetime import datetime, timezone
from pathlib import Path
import math
import sys
try:
    from mpu6050 import mpu6050
except ModuleNotFoundError as err:
    print(err)
    print("install packages with 'sudo apt install python3-smbus && pip install mpu6050-raspberrypi && pip install smbus'!")
    print("See https://github.com/m-rtijn/mpu6050")
    sys.exit(0)
import json
import time
from typing import Dict, Tuple

CALIBRATION_FILE = 'mpu6050_calibration.json'
AXIS_MAP = {
        "left": "y",
        "right": "-y",
        "top": "x",
        "bottom": "-x"
    }

# Define a function to read the sensor data
def read_sensor_data() -> Tuple[Dict, Dict, Dict]:
    """Reads the accelerometer, gyroscope, and temperature data from the MPU6050 sensor."""
    # Create a new Mpu6050 object
    sensor = mpu6050(0x68)

    # Read the sensor values
    accelerometer_data = sensor.get_accel_data()
    gyroscope_data = sensor.get_gyro_data()
    temperature = sensor.get_temp()

    return {
        'accelerometer': accelerometer_data,
        'gyroscope': gyroscope_data,
        'temperature': temperature
    }


def update_baseline(calibration_file=CALIBRATION_FILE):
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
        if Path(calibration_file).exists():
            with open(calibration_file, 'r') as f:
                existing_data = json.load(f)
            # Merge with existing data if file already exists
            calibration_data['baseline'].update(existing_data)
        with open(calibration_file, 'w') as f:
            json.dump(calibration_data, f, indent=4)
        print(f"Calibration complete. Data saved to {calibration_file}")
    except OSError:
        print("Sensor connection error during calibration.")


def interactive_axis_calibration(calibration_file=CALIBRATION_FILE):
    """
    Guides the user to move the sensor in specific directions to determine which axis
    corresponds to left/right and top/bottom. Saves the mapping to a JSON file.
    """
    print("Starting interactive axis calibration.")
    print("Please follow the instructions. Hold the sensor steady, then move it as requested.")
    axis_map = {}

    # Helper to get axis with largest change
    def get_movement_axis(baseline, moved):
        diffs = {axis: moved[axis] - baseline[axis] for axis in ['x', 'y', 'z']}
        axis = max(diffs, key=lambda k: abs(diffs[k]))
        sign = 1 if diffs[axis] > 0 else -1
        return axis if sign > 0 else f"-{axis}"

    # Baseline reading
    input("Place the sensor flat and still, then press Enter...")
    baseline = read_sensor_data()
    baseline_accel = baseline['accelerometer'] 
    print(f"Baseline: {baseline_accel}")

    # Left movement
    input("Tilt the sensor LEFT, then press Enter...")
    left = read_sensor_data()['accelerometer']
    axis_map['left'] = get_movement_axis(baseline_accel, left)
    print(f"Detected axis for LEFT: {axis_map['left']}")

    # Right movement
    input("Tilt the sensor RIGHT, then press Enter...")
    right = read_sensor_data()['accelerometer']
    axis_map['right'] = get_movement_axis(baseline_accel, right)
    print(f"Detected axis for RIGHT: {axis_map['right']}")

    # Top movement
    input("Tilt the sensor TOP (away from you), then press Enter...")
    top = read_sensor_data()['accelerometer']
    axis_map['top'] = get_movement_axis(baseline_accel, top)
    print(f"Detected axis for TOP: {axis_map['top']}")

    # Bottom movement
    input("Tilt the sensor BOTTOM (towards you), then press Enter...")
    bottom = read_sensor_data()['accelerometer']
    axis_map['bottom'] = get_movement_axis(baseline_accel, bottom)
    print(f"Detected axis for BOTTOM: {axis_map['bottom']}")

    # Save mapping
    mapping = {
        "baseline": baseline,
        "axis_map": axis_map,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    mapping_file = calibration_file
    with open(mapping_file, 'w') as f:
        json.dump(mapping, f, indent=4)
    print(f"Axis mapping saved to {mapping_file}")


def get_calibration_data(calibration_file=CALIBRATION_FILE):
    """
    Reads the calibration data from the specified file.
    Returns a dict with accelerometer, gyroscope, axis references data.
    """
    try:
        with open(calibration_file, 'r') as f:
            calibration_data = json.load(f)
        return calibration_data
    except FileNotFoundError:
        print(f"Calibration file '{calibration_file}' not found.")
        return None


def get_calibrated_sensor_data(calibration_file=CALIBRATION_FILE):
    """
    Reads current sensor data and calibration zero from file,
    returns a dict with calibrated values (current - sensor_reference).
    """
    # Read current sensor data
    current_data = read_sensor_data()

    # Read calibration zero from file
    sensor_reference = get_calibration_data(calibration_file)
    if sensor_reference is None:
        print("Calibration data not found. Please calibrate the sensor first.")
        return None

    # Subtract calibration zero from current data
    calibrated = {
        'accelerometer': {
            axis: current_data['accelerometer'][axis] - sensor_reference['baseline']['accelerometer'][axis]
            for axis in current_data['accelerometer']
        },
        'gyroscope': {
            axis: current_data['gyroscope'][axis] - sensor_reference['baseline']['gyroscope'][axis]
            for axis in current_data['gyroscope']
        },
        'temperature': current_data['temperature']
    }
    return calibrated

def detect_tilt_threshold(calibrated_data, axis_map=AXIS_MAP, threshold=3.0):
    """
    Detects tilt direction based on calibrated accelerometer data.
    Returns one of: 'left', 'right', 'top', 'bottom', or None if no significant tilt.
    threshold: minimum absolute value (in m/s^2) to consider as a tilt.
    """
    accel = calibrated_data['accelerometer']
    max_value = 0
    max_direction = None
    for direction, axis_signed in axis_map.items():
        sign = -1 if axis_signed.startswith('-') else 1
        axis = axis_signed if sign > 0 else axis_signed[1:]
        value = accel[axis]
        max_value = max(max_value, value * sign)
        max_direction = max_direction if max_value > value * sign else direction
    if max_value > threshold:
        return max_direction
    return None


def detect_knock(calibrated_data, axis_map: Dict =AXIS_MAP, accel_threshold=5.0):
    """
    Detects a knock direction based on a sudden spike in calibrated accelerometer data.
    Returns one of: 'knock_left', 'knock_right', 'knock_top', 'knock_bottom', or None if no knock detected.
    accel_threshold: minimum absolute acceleration (in m/s^2) to consider as a knock.
    Uses axis_map for flexible axis/sign mapping.
    """
    accel = calibrated_data['accelerometer']
    max_value = 0
    max_direction = None
    for direction, axis_signed in axis_map.items():
        sign = -1 if axis_signed.startswith('-') else 1
        axis = axis_signed if sign > 0 else axis_signed[1:]
        value = accel[axis]
        max_value = max(max_value, value * sign)
        max_direction = max_direction if max_value > value * sign else direction
    if max_value > accel_threshold:
        return f"knock_{max_direction}"
    return None


def detect_knock_peak(prev_data, curr_data, prev_time, curr_time, 
             axis_map = AXIS_MAP, rate_threshold=30.0, magnitude_threshold=8.0, max_duration=0.2):
    """
    Robust knock detection using rate of change, magnitude, and duration.
    """
    dt = curr_time - prev_time
    if dt == 0 or dt > max_duration:
        return None

    prev_accel = prev_data['accelerometer']
    curr_accel = curr_data['accelerometer']

    # Rate of change (derivative)
    dx = (curr_accel['x'] - prev_accel['x']) / dt
    dy = (curr_accel['y'] - prev_accel['y']) / dt
    dz = (curr_accel['z'] - prev_accel['z']) / dt

    # Magnitude of acceleration
    mag = math.sqrt(curr_accel['x']**2 + curr_accel['y']**2 + curr_accel['z']**2)

    axis_to_direction = {value: key for key, value in axis_map.items()}
    def get_sign_str(value):
        return "-" if value < 0 else ""

    # High-pass: require both a sharp rate and a high magnitude
    if (abs(dx) > rate_threshold or abs(dy) > rate_threshold or abs(dz) > rate_threshold) and mag > magnitude_threshold:
        # return direction based on which axis had the highest rate
        axis = max(('x', abs(dx)), ('y', abs(dy)), key=lambda t: t[1])[0]
        dmax = max(abs(dx), abs(dy))
        
        return f'knock_{axis_to_direction[get_sign_str(dmax) + axis]}'
        if axis == 'y' and  dy > 0:
            return f'knock_left' if dy > 0 else 'knock_right'
    return None


if __name__ == "__main__":
    # Check if the script is run with 'calibrate' argument
    if len(sys.argv) > 1 and sys.argv[1] == 'calibrate':
        interactive_axis_calibration()
        print("Interactive axis calibration complete. Please run the script again to read sensor data.")
        sys.exit(0)
    
    # Start a while loop to continuously read the sensor data
    try:
        # os.system('clear')
        prev_data = None
        prev_time = time.time()
        while True:
            try:
                import json
                # current_data = read_sensor_data()
                current_data = get_calibrated_sensor_data()
                os.system('clear')
                print("Current sensor data:", json.dumps(current_data, indent=4))
                detect_tilt_threshold_result = detect_tilt_threshold(current_data)
                print("Tilt threshold detection result:", detect_tilt_threshold_result)
                detect_knock_result = detect_knock(current_data)
                print("Knock detection result:", detect_knock_result)
                curr_time = time.time()
                prev_data = prev_data or read_sensor_data()
                if prev_data is not None:
                    knock_peak_result = detect_knock_peak(prev_data, current_data, prev_time, curr_time)
                    print("Knock peak detection result:", knock_peak_result)
                if knock_peak_result:
                    time.sleep(1)
                prev_data = current_data
                prev_time = curr_time
            except OSError:
                os.system('clear')
                print("Connection lost. Retry")
            # time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping due to keyboard interrupt.")
        sys.exit(0)
