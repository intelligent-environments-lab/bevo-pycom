# bevo-pycom

### To-do:

* ~~CO2 Sensor~~

* Whatever else sensors

* ~~Integrate sensor code with completed LoRa code~~
   * ~~Need to figure out packet structure to send via LoRa~~
   * ~~DR3 can only send 200 or so bits (??) per message~~ it's actually 242 bytes but a lil less
   

* ~~Temporary storage code (maybe save most recent 5000 records??)~~ LOW PRIORITY
   
### Completed:

* SPS30 I2C Driver
* SCD30 I2C Driver -- UNTESTED
* LoRa publishing code -- UNTESTED


Sensirion SPS30 datasheet: [link](https://cdn.sparkfun.com/assets/2/d/2/a/6/Sensirion_SPS30_Particulate_Matter_Sensor_v0.9_D1__1_.pdf)
