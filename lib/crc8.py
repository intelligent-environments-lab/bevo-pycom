# Author: Tung To
# Init: 0xFF
# Poly: 0x31
import ubinascii

def calc_crc8(data):
    crc = 0xFF
    for i in range(0, 2):
        crc ^= data[i]
        for j in range(8, 0, -1):
            if(crc & 0x80):
                crc = (crc << 1) ^ 0x31
            else:
                crc = (crc << 1)

    return ubinascii.unhexlify(hex(crc)[-2:])
