import time
import os
from gpiozero import RGBLED
from ina219 import INA219
import subprocess
import re

# LED cathode
# long leg -> GND
# R/G/B -> 330 ohm -> GPIO

# INA219 Setup
SHUNT_OHMS = 0.1
ina = INA219(SHUNT_OHMS, address=0x40, busnum=1)
ina.configure()

# LED Setup
LED = RGBLED(red=0, green=5, blue=6)
intensity = 0.1

# Voltage thresholds
WARNING = 4.9   # V
CRITICAL = 4.7  # V
SHUTDOWN = 4.6  # V

shutdown_start = None  # Time when shutdown sequence started


def led_blink(interval=0.5):
    color = LED.color
    LED.off()
    time.sleep(interval)
    LED.color = color


def get_signal_strength():
    try:
        output = subprocess.check_output(["iwconfig", "wlan0"]).decode()
        match = re.search(r"Signal level=(-\d+) dBm", output)
        if match:
            return int(match.group(1))  # z. B. -40 bis -90 dBm
    except subprocess.CalledProcessError:
        return None


try:
    LED.color = (intensity, 0, 0)  # Start with red
    sleep_interval = 1.0
    while True:
        voltage = ina.voltage()
        wlan_signal = get_signal_strength()
        print(f"Akkuspannung: {voltage:.2f} V, wlan signal: {wlan_signal} dBm")

        if (not wlan_signal) or (wlan_signal < -80):
            LED.color = (intensity, 0, 0)
        elif -60 >= wlan_signal >= -80:
            LED.color = (intensity, intensity * 0.25, 0)
        elif wlan_signal > -60:
            LED.color = (0, intensity, 0)
        if voltage < SHUTDOWN:
            if shutdown_start is None:
                shutdown_start = time.time()
            else:
                elapsed = time.time() - shutdown_start
                if elapsed > 300:  # 5 minutes
                    print(">>> Battery critical. Raspberry Pi shutting down! <<<")
                    os.system("sudo shutdown now")
            sleep_interval = 0.3
            led_blink(sleep_interval)
        elif voltage < CRITICAL:
            shutdown_start = None
            sleep_interval = 0.5
            led_blink(sleep_interval)

        time.sleep(sleep_interval)

except KeyboardInterrupt:
    print("Shut down program...")

finally:
    LED.off()
