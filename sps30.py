# Author: Tung To
#
# class methods:
# - start()
# - stop()
# - get_packed_msg()
#
# start() should be run from a separate thread so that stop() can update exit flag

from machine import I2C
import ubinascii
import time
import struct
from crc8 import calc_crc8

# SPS30 I2C ID
SPS30_I2C_ID = 0x69

# SPS30 I2C COMMANDS
SPS30_START_ADDR    = b'\x00\x10'
SPS30_READY_ADDR    = b'\x02\x02'
SPS30_READ_ADDR     = b'\x03\x00'
SPS30_STOP_ADDR     = b'\x01\x04'
SPS30_RESET_ADDR    = b'\xD3\x04'

# SPS I2C COMMAND OPTIONS
SPS30_START_MEASUREMENT = b'\x03\x00'

# SPS30_1 PINS
SPS30_SDA = 'P10'
SPS30_SCL = 'P11'

class sps30:

    _i2c = None
    _interval = None
    _curr_data = [None] * 10

    _exit_flag = False

    def __init__(self, b=1, p=(SPS30_SDA, SPS30_SCL), br=20000, interval=10):

        self._interval = interval
        self._i2c = I2C(b, pins=p, baudrate=br)
        #assert SPS30_I2C_ID in self._i2c.scan(), "SPS30 not connected."
        while SPS30_I2C_ID not in self._i2c.scan():
            print("SPS30 not connected.")
            time.sleep(3)

        self._send_start()


    def start(self):

        # Main operating loop
        while not self._exit_flag:

            try:

                # Polls until ready
                while not(self._is_ready()):
                    time.sleep(0.1)

                # Sample sps30
                read = self._read_data()

                # Check crc8 and deserialize
                for i in range(0, 10):

                    # crc8 check
                    assert calc_crc8(read[i * 6 : i * 6 + 2]) == bytes([read[i * 6 + 2]]), "Bad upper crc8"
                    assert calc_crc8(read[i * 6 + 3: i * 6 + 5]) == bytes([read[i * 6 + 5]]), "Bad lower crc8"

                    # Deserialize
                    float_struct = struct.pack('>BBBB', read[i * 6], read[i * 6 + 1], read[i * 6 + 3], read[i * 6 + 4])
                    self._curr_data[i] = struct.unpack('>f', float_struct)[0]

                # Sleep timer
                time.sleep(self._interval)

            except Exception as e:
                # Reset sensor in case I2C Bus fail, bad crc8, whatever
                print(e)
                self._reset()
                time.sleep(3)


    # Called in a separate thread
    def stop(self):

        self._i2c.writeto(SPS30_I2C_ID, SPS30_STOP_ADDR)
        self._i2c.deinit()
        self._exit_flag = True

    # Serialize data for transmission
    # Call from main thread
    # Payload size: 40 bytes
    def get_packed_msg(self):
        return struct.pack('<ffffffffff', self._curr_data[0], self._curr_data[1],self. _curr_data[2],
                self._curr_data[3], self._curr_data[4], self._curr_data[5], self._curr_data[6], self._curr_data[7],
                self._curr_data[8], self._curr_data[9])

    def _send_start(self):

        # Start measurement mode, returns number of bytes written
        return self._i2c.writeto(SPS30_I2C_ID, SPS30_START_ADDR + SPS30_START_MEASUREMENT + calc_crc8(SPS30_START_MEASUREMENT))

    def _is_ready(self):

        # Returns device ready flag
        self._i2c.writeto(SPS30_I2C_ID, SPS30_READY_ADDR)
        read = self._i2c.readfrom(SPS30_I2C_ID, 3)

        return bytes([read[2]]) == calc_crc8(read[0:2])

    def _read_data(self):

        # Returns read data
        self._i2c.writeto(SPS30_I2C_ID, SPS30_READ_ADDR)
        return self._i2c.readfrom(SPS30_I2C_ID, 60)

    def _reset(self):

        # Resets sensor
        self._i2c.writeto(SPS30_I2C_ID, SPS30_RESET_ADDR)

    # DEBUGGING ONLY, SHOULD LOG DATA
    def _print(self):
        print('PM 0.5 conc.: {} cm-3'.format(_curr_data[4]))
        print('PM 1.0 conc.: {} cm-3\tMass conc.: {} ug/m3'.format(_curr_data[5], _curr_data[0]))
        print('PM 2.5 conc.: {} cm-3\tMass conc.: {} ug/m3'.format(_curr_data[6], _curr_data[1]))
        print('PM 4.0 conc.: {} cm-3\tMass conc.: {} ug/m3'.format(_curr_data[7], _curr_data[2]))
        print('PM 10. conc.: {} cm-3\tMass conc.: {} ug/m3'.format(_curr_data[8], _curr_data[3]))
        print('Typical particle size: {} um'.format(_curr_data[9]))
