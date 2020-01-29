import _thread
import time
import ubinascii
import socket
import struct
import pycom
from network import LoRa
from sps30 import sps30
from scd30 import scd30

# create an OTA authentication params
dev_eui = ubinascii.unhexlify('70B3D54994CBFEDA')
app_key = ubinascii.unhexlify('70B3D57ED002722C')
nwk_key = ubinascii.unhexlify('ADFCEABE7B6F8AFFCA503ABC0310C871')

# TTN params (2nd subband)
LORA_FREQUENCY = 903900000
LORA_DR = 1

# Sensor flags
using_pm = False
using_co2 = False
using_pysense_sensor = True

if using_pysense_sensor:
    from pysense import Pysense
    from LIS2HH12 import LIS2HH12
    from SI7006A20 import SI7006A20
    from LTR329ALS01 import LTR329ALS01
    from MPL3115A2 import MPL3115A2,ALTITUDE,PRESSURE

def main():

    pycom.heartbeat(False)

    # Sensor initializations with default params
    # bus   = 1
    # sda   = P10
    # scl   = P11
    # baud  = 20000
    # interval  = 10
    pm_sensor = sps30() if using_pm else None
    co2_sensor = scd30() if using_co2 else None

    # Start sensors in a separate thread
    pm_thread = _thread.start_new_thread(pm_sensor.start, ()) if using_pm else None
    co2_thread = _thread.start_new_thread(co2_sensor.start, ()) if using_co2 else None

    # Prepare LoRa channels
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.US915, device_class=LoRa.CLASS_C)
    prepare_channels(lora, LORA_FREQUENCY)
    #lora = LoRa(mode=LoRa.LORA, region=LoRa.US915, frequency=904600000, bandwidth=LoRa.BW_500KHZ, sf=8)
    # Join LoRa network with OTAA
    lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_key, nwk_key), timeout=0, dr=0)
    # wait until the module has joined the network
    print('Over the air network activation ... ', end='')
    while not lora.has_joined():
        time.sleep(2.5)
        print('.', end='')
    print('')

    # Socket initializations
    lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    lora_socket.setsockopt(socket.SOL_LORA, socket.SO_DR, LORA_DR)
    # msg are confirmed at the FMS level
    lora_socket.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, False)
    # make the socket non blocking by default
    lora_socket.setblocking(False)

    lora.callback(trigger=( LoRa.RX_PACKET_EVENT |
                            LoRa.TX_PACKET_EVENT |
                            LoRa.TX_FAILED_EVENT  ), handler=lora_cb)

    time.sleep(4) # this timer is important and caused me some trouble ...

    # Send pm (payload=40bytes) and co2 (payload=12bytes) data every 5 minutes
    while True:
        # Poll data
        if using_pm:
            pm_data = pm_sensor.get_packed_msg()
        if using_co2:
            co2_data = co2_sensor.get_packed_msg()
        if using_pysense_sensor:
            py = Pysense()
            mp = MPL3115A2(py,mode=ALTITUDE) # Returns height in meters. Mode may also be set to PRESSURE, returning a value in Pascals
            si = SI7006A20(py)
            lt = LTR329ALS01(py)
            li = LIS2HH12(py)

        # Send data
        if using_pm:
            send_pkt(lora_socket,pm_data, 8)
        if using_co2:
            send_pkt(lora_socket, co2_data, 9)
        if using_pysense_sensor:

            temp = si.temperature()
            rh = si.humidity()
            rlux = lt.light()[0]
            blux = lt.light()[1]

            pysense_pkt = struct.pack('<ffii', temp, rh, rlux, blux)
            send_pkt(lora_socket, pysense_pkt, 10)

        time.sleep(15 - using_pm * 5 - using_co2 * 5 - using_pysense_sensor * 5)

    # Stop polling and end threads
    if using_pm:
        pm_sensor.stop()
    if using_co2:
        co2_sensor.stop()

'''
    utility function to setup the lora channels
    completely rewritten from example code for TTN
'''
def prepare_channels(lora, base_freq):

    # Technically there are only channels 0-71 but seems like lora library is bugged and channel 72 exists @ 914.2 MHz
    for index in range(0, 72):
        lora.remove_channel(index)

    for i in range(0, 8):
        fq = base_freq + (i * 200000)
        lora.add_channel(i + 8, frequency=fq, dr_min=0, dr_max=3)
        print("US915 Adding channel up %s %s" % (i + 8, fq))

    if (LORA_DR == 4):
        lora.add_channel(65, frequency=904600000, dr_min=0, dr_max=4)
        print("US915 Adding channel up 65 904600000")

'''
    call back for handling RX packets
'''
def lora_cb(lora):
    events = lora.events()
    if events & LoRa.RX_PACKET_EVENT:
        if lora_socket is not None:
            frame, port = lora_socket.recvfrom(512) # longuest frame is +-220
            print(port, frame)
    if events & LoRa.TX_PACKET_EVENT:
        #print("tx_time_on_air: {} ms @ dr {}".format(lora.stats().tx_time_on_air, lora.stats().sftx))
        print("Frequency transmitted: {}".format(lora.stats().tx_frequency))
    if events & LoRa.TX_FAILED_EVENT:
        print("Failed to send packet")

'''
    sending lora packet over a specific port
'''
def send_pkt(lora_socket, pkt, port):
    # LED while transmitting
    # SPS30: lime
    # SCD30: teal
    # Pysense: fuchsia
    if port == 8:
        pycom.rgbled(0x00FF00)
    if port == 9:
        pycom.rgbled(0x00FFFF)
    if port == 10:
        pycom.rgbled(0xFF00FF)

    lora_socket.bind(port)
    lora_socket.send(pkt)
    time.sleep(5) # timer probably necessary.. idk how long tho

    # turn off LED
    pycom.rgbled(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exited.")
