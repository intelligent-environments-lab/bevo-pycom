# bevo-pycom

### To-do:

* CO sensor

* Whatever else sensors

* Integrate sensor code with completed LoRa code
   * Need to figure out packet structure to send via LoRa
   * DR3 can only send 200 or so bits (??) per message
   
* Temporary storage code (maybe save most recent 5000 records??)
   * Could potentially use local database for read/write efficiency
   * Can lopy4's processor even handle this??
   * File write -> FTP Server
   
### Completed:

* SPS30 I2C Driver

Sensirion SPS30 datasheet: [link](https://cdn.sparkfun.com/assets/2/d/2/a/6/Sensirion_SPS30_Particulate_Matter_Sensor_v0.9_D1__1_.pdf)
