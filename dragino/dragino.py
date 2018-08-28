#!/usr/bin/env python3
"""
Basic interface for dragino LoRa/GPS HAT
Copyright (C) 2018 Philip Basford

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from random import randrange
from datetime import datetime, timedelta
import logging
import os.path
from configobj import ConfigObj
from serial import Serial
import pynmea2
from .SX127x.LoRa import LoRa, MODE
from .SX127x.board_config import BOARD
from .LoRaWAN import new as lorawan_msg
from .LoRaWAN import MalformedPacketException
from .LoRaWAN.MHDR import MHDR
from .FrequncyPlan import LORA_FREQS

DEFAULT_LOG_LEVEL = logging.WARN #Change after finishing development
DEFAULT_RETRIES = 3 # How many attempts to send the message

AUTH_ABP = "ABP"
AUTH_OTTA = "OTTA"

class Dragino(LoRa):
    """
        Class to provide an interface to the dragino LoRa/GPS HAT
    """
    def __init__(
            self, config_filename, freqs=LORA_FREQS,
            logging_level=DEFAULT_LOG_LEVEL,
            lora_retries=DEFAULT_RETRIES):
        """
            Create the class to interface with the board
        """
        self.logger = logging.getLogger("Dragino")
        self.logger.setLevel(logging_level)
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
        BOARD.setup()
        super(Dragino, self).__init__(logging_level < logging.INFO)
        self.devnonce = [randrange(256), randrange(256)] #random nonce
        self.logger.debug("Nonce = %s", self.devnonce)
        self.freqs = freqs
        #Set all auth method tockens to None as not sure what auth method we'll use
        self.device_addr = None
        self.network_key = None
        self.apps_key = None
        self.appkey = None
        self.appeui = None
        self.deveui = None
        self.config = DraginoConfig(config_filename, logging_level)
        self.lora_retries = lora_retries
        self._read_frame_count()
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([1, 0, 0, 0, 0, 0])
        freq = freqs[randrange(len(freqs))]#Pick a random frequency
        self.set_freq(freq)
        self.logger.info("Frequency = %s", freq)
        self.set_pa_config(pa_select=1)
        self.set_spreading_factor(self.config.spreading_factor)
        self.set_pa_config(
            max_power=self.config.max_power,
            output_power=self.config.output_power)
        self.set_sync_word(self.config.sync_word)
        self.set_rx_crc(self.config.rx_crc)
        if self.config.auth == AUTH_ABP:
            self.device_addr = self.config.devaddr
            self.network_key = self.config.nwskey
            self.apps_key = self.config.appskey
        elif self.config.auth == AUTH_OTTA:
            self.appeui = self.config.appeui
            self.deveui = self.config.deveui
            self.appkey = self.config.appkey
        assert self.get_agc_auto_on() == 1
        self.gps_serial = Serial(
            self.config.gps_serial_port,
            self.config.gps_baud_rate,
            timeout=self.config.gps_serial_timeout)
        self.gps_serial.flush()

    def _read_frame_count(self):
        """
            Read the frame count from file - if no file present assume it's 1
        """
        if not os.path.isfile(self.config.fcount_filename):
            self.logger.warning("No frame count file available")
            self.frame_count = 1
        else:
            self.logger.info("Reading Frame count from: %s", self.config.fcount_filename)
            try:
                with open(self.config.fcount_filename, "r") as f_handle:
                    self.frame_count = int(f_handle.readline())
                    self.logger.info("Frame count = %d", self.frame_count)
            except (IOError, ValueError) as exp:
                self.logger.error("Unable to open fcount file. Resettting count")
                self.logger.error(str(exp))
                self.frame_count = 1

    def _save_frame_count(self):
        """
            Saves the frame count out to file so that check in ttn can be enabled
            If the file doesn't exist then create it
        """
        try:
            with open(self.config.fcount_filename, "w") as f_handle:
                f_handle.write('%d\n' % self.frame_count)
                f_handle.close()
                self.logger.debug(
                    "Frame count %d saved to %s",
                    self.frame_count, self.config.fcount_filename)
        except IOError as err:
            self.logger.error("Unable to save frame count: %s", str(err))

    def on_rx_done(self):
        """
            Callback on RX complete, signalled by I/O
        """
        self.logger.debug("Recieved message")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        lorawan = lorawan_msg([], self.appkey)
        lorawan.read(payload)
        lorawan.get_payload()
#        print(lorawan.get_mhdr().get_mversion())
        if lorawan.get_mhdr().get_mtype() == MHDR.JOIN_ACCEPT:
            self.logger.debug("Join resp")
            #It's a response to a join request
            lorawan.valid_mic()
            self.device_addr = lorawan.get_devaddr()
            self.logger.info("Device: %s", self.device_addr)
            self.network_key = lorawan.derive_nwskey(self.devnonce)
            self.logger.info("Network key: %s", self.network_key)
            self.apps_key = lorawan.derive_appskey(self.devnonce)
            self.logger.info("APPS key: %s", self.apps_key)

    def on_tx_done(self):
        """
            Callback on TX complete is signaled using I/O
        """
        self.logger.debug("TX Complete")
        self.clear_irq_flags(TxDone=1)
        self.set_mode(MODE.STDBY)
        self.set_dio_mapping([0, 0, 0, 0, 0, 0])
        self.set_invert_iq(1)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)


    def join(self):
        """
            Perform the OTAA auth in order to get the keys requried to transmit
        """
        if self.config.auth == AUTH_ABP:
            self.logger.info("Using ABP no need to Join")
        elif self.config.auth == AUTH_OTTA:
            self.logger.debug("Performing OTTA Join")
            appkey = self.appkey
            appeui = self.appeui
            deveui = self.deveui
            self.logger.info("App key = %s", appkey)
            self.logger.info("App eui = %s", appeui)
            self.logger.info("Dev eui = %s", deveui)
            lorawan = lorawan_msg(appkey)
            lorawan.create(
                MHDR.JOIN_REQUEST,
                {'deveui': deveui, 'appeui': appeui, 'devnonce': self.devnonce})
            self.write_payload(lorawan.to_raw())
            self.set_mode(MODE.TX)
        else:
            self.logger.error("Unknown auth mode")
            return

    def registered(self):
        """
            Returns true if either ABP is used for auth, in which case registration
            is hardcoded, otherwise check that join has been run
        """
        return self.device_addr is not None

    def send_bytes(self, message):
        """
            Send a list of bytes over the LoRaWAN channel
        """
        attempt = 0
        if self.network_key is None or self.apps_key is None: # either using ABP / join has  run
            raise DraginoError("No network and/or apps key")
        while attempt <= self.lora_retries: # try a couple of times because of
            attempt += 1 #  intermittent malformed packets nasty hack
            try: #shouldn't be needed
                lorawan = lorawan_msg(self.network_key, self.apps_key)
                lorawan.create(
                    MHDR.UNCONF_DATA_UP,
                    {'devaddr': self.device_addr,
                     'fcnt': self.frame_count,
                     'data': message})
                self.logger.debug("Frame count %d", self.frame_count)
                self.frame_count += 1
                self._save_frame_count()
                self.write_payload(lorawan.to_raw())
                self.logger.debug("Packet = %s", lorawan.to_raw())
                self.set_dio_mapping([1, 0, 0, 0, 0, 0])
                self.set_mode(MODE.TX)
                self.logger.info(
                    "Succeeded on attempt %d/%d", attempt, self.lora_retries)
                return
            except ValueError as err:
                self.logger.error(str(err))
                raise DraginoError(str(err)) from None
            except MalformedPacketException as exp:
                self.logger.error(exp)
            except KeyError as err:
                self.logger.error(err)

    def send(self, message):
        """
            Send a string over the channel
        """
        self.send_bytes(list(map(ord, str(message))))

    def get_gps(self):
        """
            Get the GPS position from the dragino,
            waits for the specified timeout and then gives up
        """
        start = datetime.utcnow()
        end = start + timedelta(seconds=self.config.gps_wait_period)
        self.logger.info(
            "Waiting for %d seconds until %s", self.config.gps_wait_period, end)
        msg = None

        while datetime.utcnow() < end:
            try:
                # read the serial port, convert to a string
                gps_data = self.gps_serial.readline().decode()
            except UnicodeDecodeError:
                #not yet got valid data from gps
                continue
            gps_data_arr = gps_data.split(",")
            if gps_data_arr[0] == "$GPGGA": #It's a position string
                #print(gps_data)
                msg = pynmea2.parse(gps_data)
                break
        # this will be None if no message is decoded, otherwise it'll contain the information
        return msg

class DraginoError(Exception):
    """
        Error class for dragino class
    """
    pass

class DraginoConfig(object):
    """
        Reads an ini file containing the configuration for the dragino board
    """
    def __init__(self, config_file, log_level=DEFAULT_LOG_LEVEL):
        """
            Read in the config and create the object
        """
        self.logger = logging.getLogger("DraginoConfig")
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
        self.logger.setLevel(log_level)
        try:
            config = ConfigObj(config_file)
            self.gps_baud_rate = int(config["gps_baud_rate"])
            self.gps_serial_port = config["gps_serial_port"]
            self.gps_serial_timeout = int(config["gps_serial_timeout"])
            self.gps_wait_period = int(config["gps_wait_period"])
            self.spreading_factor = int(config["spreading_factor"])
            self.max_power = int(config["max_power"], 16)
            self.output_power = int(config["output_power"], 16)
            self.sync_word = int(config["sync_word"], 16)
            self.rx_crc = bool(config["rx_crc"])
            self.fcount_filename = config["fcount_filename"]
            auth = config["auth_mode"]
            if auth.upper() == "ABP":
                self.logger.info("Using ABP mode")
                self.auth = AUTH_ABP
                self.devaddr = self._convert_array(config["devaddr"])
                self.nwskey = self._convert_array(config["nwskey"])
                self.appskey = self._convert_array(config["appskey"])
            elif auth.upper() == "OTAA":
                self.logger.info("Using OTAA mode")
                self.auth = AUTH_OTTA
                self.deveui = self._convert_array(config["deveui"])
                self.appeui = self._convert_array(config["appeui"])
                self.appkey = self._convert_array(config["appkey"])
            else:
                self.logger.critical("Unsupported auth mode chosen: %s", auth)
                raise DraginoError("Unsupported auth mode")
            self.logger.debug("GPS Baud Rate: %d", self.gps_baud_rate)
            self.logger.debug("GPS Serial Port: %s", self.gps_serial_port)
            self.logger.debug("GPS Serial Timeout: %s", self.gps_serial_timeout)
            self.logger.debug("GPS Wait Period: %d", self.gps_wait_period)
            self.logger.debug("Spreading factor: %d", self.spreading_factor)
            self.logger.debug("Max Power: %02X", self.max_power)
            self.logger.debug("Output Power: %02X", self.output_power)
            self.logger.debug("Sync Word: %02X", self.sync_word)
            self.logger.debug("RX CRC: %s", str(self.rx_crc))
            self.logger.debug("Frame Count Filename: %s", self.fcount_filename)
            self.logger.debug("Auth mode: %s", self.auth)
            if self.auth == AUTH_ABP:
                self.logger.debug("Device Address: %s", str(self.devaddr))
                self.logger.debug("Network Session Key: %s", str(self.nwskey))
                self.logger.debug("App Session Key: %s", str(self.appskey))
            elif self.auth == AUTH_OTTA:
                self.logger.debug("Device EUI: %s", str(self.deveui))
                self.logger.debug("App EUI: %s", str(self.appeui))
                self.logger.debug("App Key: %s", str(self.appkey))
        except KeyError as err:
            self.logger.critical("Missing required field %s", str(err))
            raise DraginoError(err) from None
        except ValueError as err:
            self.logger.critical("Unable to parse number %s", str(err))
            raise DraginoError(err) from None

    def _convert_array(self, arr):
        """
            Takes an array of hex strings and converts them into integers
        """
        new_arr = []
        for item in arr:
            new_arr.append(int(item, 16))
        self.logger.debug("Converted %d/%d items", len(new_arr), len(arr))
        return new_arr
