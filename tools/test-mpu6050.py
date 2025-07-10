import os
import csv
from datetime import datetime, timezone
from pathlib import Path
import sys

try:
    from mpu6050 import mpu6050
except ModuleNotFoundError as err:
    print(err)
    print(
        "install packages with 'sudo apt install python3-smbus && pip install mpu6050-raspberrypi && pip install smbus'!"
    )
    print("See https://github.com/m-rtijn/mpu6050")
    sys.exit(0)
import json
import time
from typing import Dict, Tuple

CALIBRATION_FILE = "mpu6050_calibration.json"
AXIS_MAP = {"left": "y", "right": "-y", "top": "x", "bottom": "-x"}


# Define a function to read the sensor data
def read_raw_sensor_data() -> Tuple[Dict, Dict, Dict]:
    """Reads the accelerometer, gyroscope, and temperature data from the MPU6050 sensor."""
    # Create a new Mpu6050 object
    sensor = mpu6050(0x68)

    # Read the sensor values
    accelerometer_data = sensor.get_accel_data()
    gyroscope_data = sensor.get_gyro_data()
    temperature = sensor.get_temp()

    return {
        "accelerometer": accelerometer_data,
        "gyroscope": gyroscope_data,
        "temperature": temperature,
    }


def update_baseline_to_file(calibration_file=CALIBRATION_FILE):
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
        current_data = read_raw_sensor_data()
        calibration_data = {
            "accelerometer": current_data["accelerometer"],
            "gyroscope": current_data["gyroscope"],
            "temperature": current_data["temperature"],
            "timestamp": time.time(),
        }
        if Path(calibration_file).exists():
            with open(calibration_file, "r") as f:
                existing_data = json.load(f)
            # Merge with existing data if file already exists
            existing_data["baseline"].update(calibration_data)
            calibration_data = existing_data
        else:
            # Create a new structure if file does not exist
            calibration_data = {
                "baseline": calibration_data,
                "axis_map": AXIS_MAP,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        with open(calibration_file, "w") as f:
            json.dump(calibration_data, f, indent=4)
        print(f"Calibration complete. Data saved to {calibration_file}")
    except OSError:
        print("Sensor connection error during calibration.")


def interactive_axis_calibration_to_file(calibration_file=CALIBRATION_FILE):
    """
    Guides the user to move the sensor in specific directions to determine which axis
    corresponds to left/right and top/bottom. Saves the mapping to a JSON file.
    """
    print("Starting interactive axis calibration.")
    print(
        "Please follow the instructions. Hold the sensor steady, then move it as requested."
    )
    axis_map = {}

    # Helper to get axis with largest change
    def get_movement_axis(baseline, moved):
        diffs = {axis: moved[axis] - baseline[axis] for axis in ["x", "y", "z"]}
        axis = max(diffs, key=lambda k: abs(diffs[k]))
        sign = 1 if diffs[axis] > 0 else -1
        return axis if sign > 0 else f"-{axis}"

    # Baseline reading
    input("Place the sensor flat and still, then press Enter...")
    baseline = read_raw_sensor_data()
    baseline_accel = baseline["accelerometer"]
    print(f"Baseline: {baseline_accel}")

    # Left movement
    input("Tilt the sensor LEFT, then press Enter...")
    left = read_raw_sensor_data()["accelerometer"]
    axis_map["left"] = get_movement_axis(baseline_accel, left)
    print(f"Detected axis for LEFT: {axis_map['left']}")

    # Right movement
    input("Tilt the sensor RIGHT, then press Enter...")
    right = read_raw_sensor_data()["accelerometer"]
    axis_map["right"] = get_movement_axis(baseline_accel, right)
    print(f"Detected axis for RIGHT: {axis_map['right']}")

    # Top movement
    input("Tilt the sensor TOP (away from you), then press Enter...")
    top = read_raw_sensor_data()["accelerometer"]
    axis_map["top"] = get_movement_axis(baseline_accel, top)
    print(f"Detected axis for TOP: {axis_map['top']}")

    # Bottom movement
    input("Tilt the sensor BOTTOM (towards you), then press Enter...")
    bottom = read_raw_sensor_data()["accelerometer"]
    axis_map["bottom"] = get_movement_axis(baseline_accel, bottom)
    print(f"Detected axis for BOTTOM: {axis_map['bottom']}")

    # Save mapping
    mapping = {
        "baseline": baseline,
        "axis_map": axis_map,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    mapping_file = calibration_file
    with open(mapping_file, "w") as f:
        json.dump(mapping, f, indent=4)
    print(f"Axis mapping saved to {mapping_file}")


def read_calibration_data_from_file(calibration_file=CALIBRATION_FILE):
    """
    Reads the calibration data from the specified file.
    Returns a dict with accelerometer, gyroscope, axis references data.
    """
    try:
        with open(calibration_file, "r") as f:
            calibration_data = json.load(f)
        return calibration_data
    except FileNotFoundError:
        print(f"Calibration file '{calibration_file}' not found.")
        return None


def calibrate_sensor_data(raw_data, calibration_file=CALIBRATION_FILE):
    """
    Calibrates raw sensor data using the calibration data from the specified file.
    Returns a dict with calibrated values (raw - sensor_reference).
    """
    # Read calibration zero from file
    sensor_reference = read_calibration_data_from_file(calibration_file)
    if sensor_reference is None:
        print("Calibration data not found. Please calibrate the sensor first.")
        return None

    # Subtract calibration zero from raw data
    calibrated = {
        "accelerometer": {
            axis: raw_data["accelerometer"][axis]
            - sensor_reference["baseline"]["accelerometer"][axis]
            for axis in raw_data["accelerometer"]
        },
        "gyroscope": {
            axis: raw_data["gyroscope"][axis]
            - sensor_reference["baseline"]["gyroscope"][axis]
            for axis in raw_data["gyroscope"]
        },
        "temperature": raw_data["temperature"],  # Temperature is not calibrated
    }
    return calibrated


def detect_tilt_threshold(calibrated_data, axis_map=AXIS_MAP, threshold=5.0):
    """
    Detects tilt direction based on calibrated accelerometer data.
    Returns one of: 'left', 'right', 'top', 'bottom', or None if no significant tilt.
    threshold: minimum absolute value (in m/s^2) to consider as a tilt.
    """
    accel = calibrated_data["accelerometer"]
    max_value = 0
    max_direction = None
    for direction, axis_signed in axis_map.items():
        sign = -1 if axis_signed.startswith("-") else 1
        axis = axis_signed if sign > 0 else axis_signed[1:]
        value = accel[axis]
        max_value = max(max_value, value * sign)
        max_direction = max_direction if max_value > value * sign else direction
    if max_value > threshold:
        return max_direction
    return None


def detect_knock(data, axis_map: Dict = AXIS_MAP, accel_threshold=2.5):
    """
    Detects a knock direction based on a sudden spike in calibrated accelerometer data.
    Returns one of: 'knock_left', 'knock_right', 'knock_top', 'knock_bottom', or None if no knock detected.
    accel_threshold: minimum absolute acceleration (in m/s^2) to consider as a knock.
    Uses axis_map for flexible axis/sign mapping.
    """
    accel = data["accelerometer"]
    max_value = 0
    max_direction = None
    if "top" in axis_map:
        del axis_map["top"]  # Remove 'top' as it is not used for knock detection
    if "bottom" in axis_map:
        del axis_map["bottom"]  # Remove 'bottom' as it is not used for
    for direction, axis_signed in axis_map.items():
        sign = -1 if axis_signed.startswith("-") else 1
        axis = axis_signed if sign > 0 else axis_signed[1:]
        value = accel[axis]
        max_value = max(max_value, value * sign)
        max_direction = max_direction if max_value > value * sign else direction
    if max_value > accel_threshold:
        return f"knock_{max_direction}"
    return None


def lowpass_filter_3d(curr_raw: dict, prev_filtered: dict, alpha: float = 0.2) -> dict:
    """
    Applies a low-pass filter to a 3D signal (dict with keys 'x', 'y', 'z').
    alpha: smoothing factor (0 < alpha < 1), lower values = smoother output.
    Returns a new filtered dict.
    """
    return {
        axis: alpha * curr_raw[axis] + (1 - alpha) * prev_filtered[axis]
        for axis in ["x", "y", "z"]
    }


def highpass_filter_3d(
    curr_raw: dict, prev_raw: dict, prev_filtered: dict, alpha: float = 0.2
) -> dict:
    """
    Applies a high-pass filter to a 3D signal (dict with keys 'x', 'y', 'z').
    alpha: smoothing factor (0 < alpha < 1), higher values = more high-frequency passed.
    Returns a new filtered dict.
    """
    return {
        axis: alpha * (prev_filtered[axis] + curr_raw[axis] - prev_raw[axis])
        for axis in ["x", "y", "z"]
    }


def record_data(filename="sensor_data.csv", duration=5, interval=0.05):
    """Records sensor data for a specified duration and saves it to a CSV file.
    filename: name of the CSV file to save the data.
    duration: total time to record data in seconds.
    interval: time between samples in seconds (default is 0.05 for 20 Hz sampling)."""
    print(f"Recording {duration} seconds of raw sensor data to '{filename}'...")
    samples = int(duration / interval)
    with open(filename, "w", newline="") as csvfile:
        fieldnames = [
            "timestamp",
            "accel_x",
            "accel_y",
            "accel_z",
            "gyro_x",
            "gyro_y",
            "gyro_z",
            "temperature",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for _ in range(samples):
            data = read_raw_sensor_data()
            now = time.time()
            row = {
                "timestamp": now,
                "accel_x": data["accelerometer"]["x"],
                "accel_y": data["accelerometer"]["y"],
                "accel_z": data["accelerometer"]["z"],
                "gyro_x": data["gyroscope"]["x"],
                "gyro_y": data["gyroscope"]["y"],
                "gyro_z": data["gyroscope"]["z"],
                "temperature": data["temperature"],
            }
            # Convert floats to strings with ',' as decimal separator
            for key in row:
                if isinstance(row[key], float):
                    row[key] = str(row[key]).replace(".", ",")
            writer.writerow(row)
            elapsed = time.time() - now
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    print(f"Done. Data saved to {filename}.")


if __name__ == "__main__":
    # Check if the script is run with 'calibrate' argument
    if len(sys.argv) > 1 and sys.argv[1] == "calibrate":
        interactive_axis_calibration_to_file()
        print(
            "Interactive axis calibration complete. Please run the script again to read sensor data."
        )
        sys.exit(0)

    # Check if the script is run with 'record' argument
    if len(sys.argv) > 1 and sys.argv[1] == "record":
        record_data()
        print("Data record complete. Please run the script again to read sensor data.")
        sys.exit(0)

    # Start a while loop to continuously read the sensor data
    try:
        # init filter data
        prev_raw = {
            "accelerometer": {"x": 0, "y": 0, "z": 0},
            "gyroscope": {"x": 0, "y": 0, "z": 0},
        }
        prev_filtered = {
            "accelerometer": {"x": 0, "y": 0, "z": 0},
            "gyroscope": {"x": 0, "y": 0, "z": 0},
        }
        # update baseline calibration
        update_baseline_to_file()
        # main loop
        while True:
            try:
                current_raw = read_raw_sensor_data()
                current_raw = calibrate_sensor_data(current_raw)
                filtered_hp = {
                    "accelerometer": highpass_filter_3d(
                        current_raw["accelerometer"],
                        prev_raw["accelerometer"],
                        prev_filtered["accelerometer"],
                        alpha=0.2,
                    ),
                    "gyroscope": highpass_filter_3d(
                        current_raw["gyroscope"],
                        prev_raw["gyroscope"],
                        prev_filtered["gyroscope"],
                        alpha=0.2,
                    ),
                }
                os.system("clear")
                print(
                    "Current prev_filtered data:", json.dumps(prev_filtered, indent=4)
                )
                detect_tilt_threshold_result = detect_tilt_threshold(current_raw)
                print("Tilt threshold detection result:", detect_tilt_threshold_result)
                detect_knock_result = detect_knock(filtered_hp)
                print("Knock detection result:", detect_knock_result)
                if detect_knock_result:
                    time.sleep(1)
                prev_raw = current_raw
                prev_filtered = filtered_hp
            except OSError:
                os.system("clear")
                print("Connection lost. Retry")
    except KeyboardInterrupt:
        print("Stopping due to keyboard interrupt.")
        sys.exit(0)
