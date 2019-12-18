from sps30 import sps30
import _thread
import time

def main():
    pm_sensor = sps30()

    # Start in a separate thread
    pm_thread = _thread.start_new_thread(pm_sensor.start, ())

    # DEBUGGING
    print("fan started!")
    time.sleep(5)

    # Thread ends naturally
    pm_sensor.stop()

if __name__ == "__main__":
    main()
