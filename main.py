import _thread
import time
from sps30 import sps30
from scd30 import scd30

def main():

    # Sensor initializations
    pm_sensor = sps30()
    co2_sensor = scd30()

    # Start in a separate thread
    pm_thread = _thread.start_new_thread(pm_sensor.start, ())
    co2_thread = _thread.start_new_thread(co2_sensor.start, ())

    # DEBUGGING
    print("Sensors running for 5 seconds")
    time.sleep(5)

    # End threads
    pm_sensor.stop()
    co2_sensor.stop()

if __name__ == "__main__":
    main()
