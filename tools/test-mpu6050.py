import mpu6050
import sys
import time


# Define a function to read the sensor data
def read_sensor_data():
    # Create a new Mpu6050 object
    sensor = mpu6050.mpu6050(0x68)

    # Read the accelerometer values
    accelerometer_data = sensor.get_accel_data()

    # Read the gyroscope values
    gyroscope_data = sensor.get_gyro_data()

    # Read temp
    temperature = sensor.get_temp()

    return accelerometer_data, gyroscope_data, temperature


def read_and_print():
    # Read the sensor data
    try:
        accelerometer_data, gyroscope_data, temperature = read_sensor_data()
        # Print the sensor data
        print("Accelerometer data:", accelerometer_data)
        print("Gyroscope data:", gyroscope_data)
        print("Temp:", temperature)
    except OSError:
        print("Connection lost. Retry")

    # Wait for 1 second
    time.sleep(1)


# Start a while loop to continuously read the sensor data
while True:
    try:
        read_and_print()
    except KeyboardInterrupt:
        print("Stopping due to keyboard interrupt.")
        sys.exit(0)
