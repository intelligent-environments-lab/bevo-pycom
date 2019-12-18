import _thread
import time
from network import LoRa
from sps30 import sps30
from scd30 import scd30

# create an OTA authentication params
dev_eui = '70B3D54994CBFEDA'
app_key = '70B3D57ED002722C'
nwk_key = 'ADFCEABE7B6F8AFFCA503ABC0310C871'

# TTN params (2nd subband)
LORA_FREQUENCY = 903900000
LORA_DR = 3

lora_socket = None
lora = None

def main():

    # Sensor initializations with default params
    # bus   = 1
    # sda   = P10
    # scl   = P11
    # baud  = 20000
    # inter = 10
    pm_sensor = sps30()
    co2_sensor = scd30()

    # Start sensors in a separate thread
    pm_thread = _thread.start_new_thread(pm_sensor.start, ())
    co2_thread = _thread.start_new_thread(co2_sensor.start, ())

    # DEBUGGING
    print("Sensors running for 5 seconds")
    time.sleep(5)

    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.US915, device_class=LoRa.CLASS_C)
    # Join LoRa network with OTAA
    lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_key, nwk_key), timeout=0, dr=0) # US915 always joins at DR0 ??
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
    lora_socket.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, 0)
    # make the socket non blocking by default
    lora_socket.setblocking(False)

    lora.callback(trigger=( LoRa.RX_PACKET_EVENT |
                            LoRa.TX_PACKET_EVENT |
                            LoRa.TX_FAILED_EVENT  ), handler=lora_cb)

    time.sleep(4) # this timer is important and caused me some trouble ...

    # Send pm (payload=80bytes) and co2 (payload=24bytes) data every 5 minutes
    while True:
        pm_data = pm_sensor.get_packed_msg()
        co2_data = co2_sensor.get_packed_msg()

        send_pkt(pm_data, 8)
        send_pkt(co2_data, 9)

        time.sleep(300 - 10)

    # Stop polling and end threads
    pm_sensor.stop()
    co2_sensor.stop()

'''
    utility function to setup the lora channels
    completely rewritten from example code for TTN
'''
def prepare_channels(lora, base_freq, dr):
    for index in range(0, 71):
        lora.remove_channel(index)

    for i in range(0, 8):
        fq = base_freq + (i * 200000)
        lora.add_channel(i + 8, frequency=fq, dr_min=0, dr_max=dr)
        print("US915 Adding channel up %s %s" % (i + 8, fq))

'''
    call back for handling RX packets
'''
def lora_cb(lora):
    events = lora.events()
    if events & LoRa.RX_PACKET_EVENT:
        if lora_socket is not None:
            frame, port = lora_socket.recvfrom(512) # longuest frame is +-220
            print(port, frame)
    #if events & LoRa.TX_PACKET_EVENT:
        #print("tx_time_on_air: {} ms @ dr {}".format(lora.stats().tx_time_on_air, lora.stats().sftx))
        #print("Frequency transmitted: {}".format(self.lora.stats().tx_frequency))

'''
    sending lora packet over a specific port
'''
def send_pkt(pkt, port):
    lora_socket.bind(port)
    lora_socket.send(pkt)
    time.sleep(5) # timer probably necessary.. idk how long tho

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exited.")
