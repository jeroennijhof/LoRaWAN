# LoRaWAN
This is a LoRaWAN v1.0 implementation in python for the Dragino LoRa/GPS HAT, it is currently being used to connect to the things network https://thethingsnetwork.org.  It is based on work at https://github.com/jeroennijhof/LoRaWAN

It uses https://github.com/mayeranalytics/pySX127x.

See: https://www.lora-alliance.org/portals/0/specs/LoRaWAN%20Specification%201R0.pdf

## Hardware Needed
* Raspberry Pi
* SD card
* LoRa/GPS HAT

## Installation
1. Install Raspbian on the Raspberry Pi
2. Enable SPI using raspi-config
3. Enable Serial using raspi-config (no login shell)
4. Install the required packages `sudo apt install device-tree-compiler git python3-crypto python3-nmea2 python3-rpi.gpio python3-serial python3-spidev python3-configobj`
5. Download the git repo `git clone https://github.com/computenodes/LoRaWAN.git`
6. Enable additional CS lines (See section below for explanation)
    1. Change into the overlay directory `cd LoRaWAN/overlay`
    2. Compile the overlay `dtc -@ -I dts -O dtb -o spi-gpio-cs.dtbo spi-gpio-cs-overlay.dts`.  This might generate a couple of warnings, but seems to work ok
    3. Copy the output file to the required folder `sudo cp spi-gpio-cs.dtbo /boot/overlays/`
    4. Enable the overlay at next reboot `echo "dtoverlay=spi-gpio-cs" | sudo tee -a /boot/config.txt`
    5. Reboot the Pi `sudo reboot`
    6. Check that the new cs lines are enabled `ls /dev/spidev0.*` should output `/dev/spidev0.0  /dev/spidev0.1  /dev/spidev0.2`.  In which case the required SPI CS line now exists
7. Create a new device in The Things Network console and copy the details into the config file
8. Run the test programm `./test.py` and the device should transmit on the things network using OTAA authentication

## Additional Chip Select Details
For some reason the Dragino board does not use one of the standard chip select lines for the SPI communication.  This can be overcome by using a device tree overlay to configure addtional SPI CS lines.  I am not a device tree expert so I adapted the example given at https://www.raspberrypi.org/forums/viewtopic.php?f=63&t=157994 to provide the code needed for this to work.  


## TODO
* Make code more readable and easier to use (From upstream)
* Add GPS code into dragino class
* Use .ini files for config not .py
* investigate device tree compilation warnings
* Test recieving of messages
