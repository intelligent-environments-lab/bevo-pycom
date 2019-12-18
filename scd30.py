# Author: Tung To
#
# class methods:
# - start()
# - stop()
#
# start() should be run from a separate thread so that stop() can update exit flag

from machine import I2C
import ubinascii
import time
import struct
from crc8 import calc_crc8

# SCD30 I2C ID
SCD30_I2C_ID = 0x61

# SCD30 I2C COMMANDS
SCD30_START_ADDR    = b'\x00\x10'
SCD30_READY_ADDR    = b'\x02\x02'
SCD30_READ_ADDR     = b'\x03\x00'
SCD30_STOP_ADDR     = b'\x01\x04'

# SPS I2C COMMAND OPTIONS
SCD30_START_MEASUREMENT = b'\x03\x00'

# SCD30_1 PINS
SCD30_1_SDA = 'P10'
SCD30_1_SCL = 'P11'

class scd30:

    _i2c = None
    _interval = None
    _curr_data = []

    _exit_flag = False

    def __init__(self, b=1, p=(SCD30_1_SDA, SCD30_1_SCL), br=20000, interval=10):

        self._interval = interval
        self._i2c = I2C(b, pins=p, baudrate=br)
        assert SCD30_I2C_ID in self._i2c.scan(), "SCD30 not connected."

        self._send_start()


    def start(self):

        # Main operating loop
        while not self._exit_flag:

            # Polls until ready
            while not(self._is_ready()):
                time.sleep(0.1)

            # Sample SCD30
            read = self._read_data()

            # Check crc8 and deserialize
            for i in range(0, 3):

                # crc8 check
                assert calc_crc8(read[i * 6 : i * 6 + 2]) == bytes([read[i * 6 + 2]]), "Bad upper crc8"
                assert calc_crc8(read[i * 6 + 3: i * 6 + 5]) == bytes([read[i * 6 + 5]]), "Bad lower crc8"

                # Deserialize
                float_struct = struct.pack('>BBBB', read[i * 6], read[i * 6 + 1], read[i * 6 + 3], read[i * 6 + 4])
                self._curr_data.append(struct.unpack('>f', float_struct)[0])

            # Sleep timer
            time.sleep(self._interval)

    # Called in a separate thread
    def stop(self):

        self._i2c.writeto(SCD30_I2C_ID, SCD30_STOP_ADDR)
        self._i2c.deinit()
        self._exit_flag = True

    def _send_start(self):

        # Start measurement mode, returns number of bytes written
        return self._i2c.writeto(SCD30_I2C_ID, SCD30_START_ADDR + SCD30_START_MEASUREMENT + calc_crc8(SCD30_START_MEASUREMENT))

    def _is_ready(self):

        # Returns device ready flag
        self._i2c.writeto(SCD30_I2C_ID, SCD30_READY_ADDR)
        read = self._i2c.readfrom(SCD30_I2C_ID, 3)

        return bytes([read[2]]) == calc_crc8(read[0:2])

    def _read_data(self):

        # Returns read data
        self._i2c.writeto(SCD30_I2C_ID, SCD30_READ_ADDR)
        return self._i2c.readfrom(SCD30_I2C_ID, 60)

    # DEBUGGING ONLY, SHOULD LOG DATA
    def _print(self):
        print('CO2 conc.: {} ppm'.format(self._curr_data[0]))
        print('Temperature: {} C'.format(self._curr_data[1]))
        print('Humidity: {} %'.format(self._curr_data[2]))
